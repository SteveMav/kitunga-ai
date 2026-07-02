from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from config import CAMERA_INDEX, CAPTURES_DIR


def _capture_path(prefix: str = "capture") -> Path:
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    return CAPTURES_DIR / f"{prefix}_{timestamp}.jpg"


def capture_image(
    *,
    camera_index: int = CAMERA_INDEX,
    test_image_path: str | Path | None = None,
) -> Path:
    """Capture an image from a camera, or copy a fixed test image into captures."""
    if test_image_path:
        source = Path(test_image_path)
        if not source.exists():
            raise FileNotFoundError(f"Test image not found: {source}")
        destination = _capture_path("test")
        shutil.copyfile(source, destination)
        return destination

    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is missing. Install dependencies with: pip install -r requirements.txt") from exc

    camera = cv2.VideoCapture(camera_index)
    try:
        if not camera.isOpened():
            raise RuntimeError(f"Camera index {camera_index} is not available.")

        ok, frame = camera.read()
        if not ok or frame is None:
            raise RuntimeError("Camera did not return an image.")

        image_path = _capture_path()
        if not cv2.imwrite(str(image_path), frame):
            raise RuntimeError(f"Could not write capture to {image_path}")
        return image_path
    finally:
        camera.release()
