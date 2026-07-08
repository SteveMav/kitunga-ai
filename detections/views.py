from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from baskets.models import BasketSession
from baskets.serializers import BasketSessionSerializer
from baskets.services import add_detection_to_basket

from .models import DetectionEvent
from .serializers import DetectionEventSerializer
from .yolo import YoloDependencyError, YoloModelError, detect_best_label, detect_objects

MAX_CAPTURE_SIZE_BYTES = 6 * 1024 * 1024


@api_view(["GET"])
def detection_events(request):
    events = DetectionEvent.objects.select_related("basket").order_by("-created_at")[:50]
    serializer = DetectionEventSerializer(events, many=True)
    return Response(serializer.data)


@ensure_csrf_cookie
@api_view(["GET"])
def csrf_token(request):
    return Response({"csrfToken": get_token(request)})


def _safe_device_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "_" for char in value)


def _save_uploaded_frame(request, *, live: bool = False):
    image = request.FILES.get("image")
    if image is None:
        raise DjangoValidationError("Champ image requis.")

    if image.size > MAX_CAPTURE_SIZE_BYTES:
        raise DjangoValidationError("Image trop volumineuse.")

    content_type = getattr(image, "content_type", "")
    if not content_type.startswith("image/"):
        raise DjangoValidationError("Le fichier doit etre une image.")

    captures_dir = Path(settings.BASE_DIR) / "kitunga_pi_client" / "captures"
    captures_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(image.name).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"

    safe_device_id = _safe_device_id(request.POST.get("device_id", "vite-camera"))
    if live:
        filename = f"live_{safe_device_id}{suffix}"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"vite_{safe_device_id}_{timestamp}{suffix}"
    destination = captures_dir / filename

    with destination.open("wb+") as output:
        for chunk in image.chunks():
            output.write(chunk)

    return {
        "filename": filename,
        "saved_path": destination,
        "size": image.size,
        "content_type": content_type,
    }


def _yolo_error_response(error: Exception, saved: dict, response_status: int):
    return Response(
        {
            "status": "detector_unavailable",
            "detail": str(error),
            "capture": {
                "filename": saved["filename"],
                "saved_path": str(saved["saved_path"]),
            },
        },
        status=response_status,
    )


def _serialize_yolo_detection(detection):
    return {
        "label": detection.label,
        "raw_label": detection.raw_label,
        "confidence": round(detection.confidence, 4),
        "box": detection.box,
    }


@csrf_exempt
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def capture_frame(request):
    try:
        saved = _save_uploaded_frame(request)
    except DjangoValidationError as error:
        return Response({"detail": error.messages[0]}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "status": "saved",
            "filename": saved["filename"],
            "saved_path": str(saved["saved_path"]),
            "size": saved["size"],
            "content_type": saved["content_type"],
        },
        status=status.HTTP_201_CREATED,
    )


@csrf_exempt
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def capture_and_detect(request):
    basket_code = request.POST.get("basket_code", "SB-001")
    device_id = request.POST.get("device_id", "IRIUN-PC-TEST")

    try:
        saved = _save_uploaded_frame(request)
    except DjangoValidationError as error:
        return Response({"detail": error.messages[0]}, status=status.HTTP_400_BAD_REQUEST)

    try:
        detection = detect_best_label(saved["saved_path"])
    except YoloDependencyError as error:
        return _yolo_error_response(error, saved, status.HTTP_503_SERVICE_UNAVAILABLE)
    except (YoloModelError, FileNotFoundError) as error:
        return _yolo_error_response(error, saved, status.HTTP_400_BAD_REQUEST)

    response_payload = {
        "status": "detected" if detection.label else "no_object",
        "capture": {
            "filename": saved["filename"],
            "saved_path": str(saved["saved_path"]),
        },
        "detected_label": detection.label,
        "confidence": round(detection.confidence, 4),
        "basket": None,
        "detection_status": None,
        "message": "Aucun objet detecte.",
    }

    if not detection.label:
        return Response(response_payload, status=status.HTTP_200_OK)

    try:
        basket, event, _item = add_detection_to_basket(
            basket_code=basket_code,
            device_id=device_id,
            detected_label=detection.label,
            confidence=Decimal(str(round(detection.confidence, 2))),
        )
    except BasketSession.DoesNotExist:
        response_payload["message"] = "Panier introuvable."
        return Response(response_payload, status=status.HTTP_404_NOT_FOUND)

    basket = BasketSession.objects.prefetch_related("items__product").get(pk=basket.pk)
    response_payload["basket"] = BasketSessionSerializer(basket, context={"request": request}).data
    response_payload["detection_status"] = event.status
    response_payload["message"] = event.message
    return Response(response_payload, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def live_detect_frame(request):
    try:
        saved = _save_uploaded_frame(request, live=True)
    except DjangoValidationError as error:
        return Response({"detail": error.messages[0]}, status=status.HTTP_400_BAD_REQUEST)

    try:
        min_confidence = float(request.POST.get("min_confidence", "0.25"))
    except ValueError:
        min_confidence = 0.25

    try:
        detections = detect_objects(saved["saved_path"], min_confidence=min_confidence)
    except YoloDependencyError as error:
        return _yolo_error_response(error, saved, status.HTTP_503_SERVICE_UNAVAILABLE)
    except (YoloModelError, FileNotFoundError) as error:
        return _yolo_error_response(error, saved, status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "status": "detected" if detections else "no_object",
            "capture": {
                "filename": saved["filename"],
                "saved_path": str(saved["saved_path"]),
            },
            "detections": [_serialize_yolo_detection(detection) for detection in detections],
        },
        status=status.HTTP_200_OK,
    )
