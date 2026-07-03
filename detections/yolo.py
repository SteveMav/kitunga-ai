from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

from .label_catalog import canonical_label_for_model_label


class YoloDependencyError(RuntimeError):
    pass


class YoloModelError(RuntimeError):
    pass


@dataclass(frozen=True)
class YoloDetection:
    label: str | None
    confidence: float
    raw_label: str | None = None
    box: dict | None = None


_model = None


def model_path() -> Path:
    return Path(settings.BASE_DIR) / "kitunga_pi_client" / "models" / "best.pt"


def _load_model():
    global _model

    path = model_path()
    if not path.exists():
        raise YoloModelError(f"Modele YOLO introuvable: {path}")

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise YoloDependencyError(
            "Ultralytics n'est pas installe dans l'environnement Django. "
            "Lance: .\\.venv\\Scripts\\pip.exe install ultralytics opencv-python"
        ) from exc

    if _model is None:
        _model = YOLO(str(path))
    return _model


def detect_objects(image_path: str | Path, min_confidence: float = 0.0) -> list[YoloDetection]:
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image introuvable: {image_path}")

    model = _load_model()
    results = model(str(image_path), verbose=False)
    if not results:
        return []

    result = results[0]
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        return []

    image_height, image_width = result.orig_shape
    detections: list[YoloDetection] = []

    for index in range(len(boxes)):
        confidence = float(boxes.conf[index].item())
        if confidence < min_confidence:
            continue

        class_id = int(boxes.cls[index].item())
        raw_label = _label_from_class_id(result.names, class_id)
        x1, y1, x2, y2 = [float(value) for value in boxes.xyxy[index].tolist()]

        detections.append(
            YoloDetection(
                label=canonical_label_for_model_label(raw_label),
                raw_label=raw_label,
                confidence=confidence,
                box={
                    "x1": max(0.0, x1 / image_width),
                    "y1": max(0.0, y1 / image_height),
                    "x2": min(1.0, x2 / image_width),
                    "y2": min(1.0, y2 / image_height),
                    "pixel_x1": round(x1, 2),
                    "pixel_y1": round(y1, 2),
                    "pixel_x2": round(x2, 2),
                    "pixel_y2": round(y2, 2),
                },
            )
        )

    return sorted(detections, key=lambda detection: detection.confidence, reverse=True)


def detect_best_label(image_path: str | Path) -> YoloDetection:
    detections = detect_objects(image_path)
    if not detections:
        return YoloDetection(label=None, confidence=0.0)
    return detections[0]


def _label_from_class_id(names, class_id: int) -> str:
    if isinstance(names, dict):
        return str(names.get(class_id, class_id))
    return str(names[class_id])
