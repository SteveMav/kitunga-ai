from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import BasketSession
from .serializers import (
    AddDetectionSerializer,
    BasketSessionSerializer,
    RemoveItemSerializer,
    StartBasketSerializer,
)
from .services import (
    add_detection_to_basket,
    create_basket_session,
    finish_basket,
    remove_item_from_basket,
)


def _basket_queryset():
    return BasketSession.objects.prefetch_related("items__product")


def _error_response(error: DjangoValidationError, response_status=status.HTTP_400_BAD_REQUEST):
    messages = error.messages if hasattr(error, "messages") else [str(error)]
    return Response({"detail": messages[0]}, status=response_status)


def _checkout_template_url(request) -> str:
    path = reverse("checkout:checkout_detail", kwargs={"token": "__TOKEN__"})
    if settings.PUBLIC_BASE_URL:
        return f"{settings.PUBLIC_BASE_URL}{path}"
    return request.build_absolute_uri(path)


@csrf_exempt
@api_view(["POST"])
def start_basket(request):
    serializer = StartBasketSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    basket = create_basket_session(serializer.validated_data["device_id"])
    payload = BasketSessionSerializer(basket, context={"request": request}).data
    return Response(payload, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def basket_detail(request, code: str):
    basket = get_object_or_404(_basket_queryset(), code=code)
    payload = BasketSessionSerializer(basket, context={"request": request}).data
    return Response(payload)


@csrf_exempt
@api_view(["POST"])
def add_detection(request, code: str):
    serializer = AddDetectionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    try:
        basket, event, item = add_detection_to_basket(
            basket_code=code,
            device_id=data["device_id"],
            detected_label=data["detected_label"],
            confidence=data["confidence"],
        )
    except BasketSession.DoesNotExist:
        return Response({"detail": "Panier introuvable."}, status=status.HTTP_404_NOT_FOUND)

    basket.refresh_from_db()
    basket = _basket_queryset().get(pk=basket.pk)
    payload = BasketSessionSerializer(basket, context={"request": request}).data
    response_status = status.HTTP_201_CREATED if item else status.HTTP_202_ACCEPTED
    return Response(
        {
            "detection_status": event.status,
            "message": event.message,
            "basket": payload,
        },
        status=response_status,
    )


@csrf_exempt
@api_view(["POST"])
def remove_item(request, code: str):
    serializer = RemoveItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        basket = remove_item_from_basket(
            basket_code=code,
            product_id=serializer.validated_data["product_id"],
        )
    except BasketSession.DoesNotExist:
        return Response({"detail": "Panier introuvable."}, status=status.HTTP_404_NOT_FOUND)
    except DjangoValidationError as error:
        return _error_response(error)

    basket = _basket_queryset().get(pk=basket.pk)
    payload = BasketSessionSerializer(basket, context={"request": request}).data
    return Response(payload)


@csrf_exempt
@api_view(["POST"])
def finish_basket_api(request, code: str):
    checkout_template = _checkout_template_url(request)
    try:
        basket = finish_basket(basket_code=code, checkout_url=checkout_template)
    except BasketSession.DoesNotExist:
        return Response({"detail": "Panier introuvable."}, status=status.HTTP_404_NOT_FOUND)
    except DjangoValidationError as error:
        return _error_response(error)

    basket = _basket_queryset().get(pk=basket.pk)
    payload = BasketSessionSerializer(basket, context={"request": request}).data
    return Response(
        {
            "status": basket.status,
            "checkout_url": payload["checkout_url"],
            "qr_code_url": payload["qr_code_url"],
            "basket": payload,
        }
    )


def basket_screen(request, code: str):
    basket = get_object_or_404(_basket_queryset(), code=code)
    return render(request, "basket_screen.html", {"basket": basket})
