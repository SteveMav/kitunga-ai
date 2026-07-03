from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from secrets import token_urlsafe

import qrcode
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from detections.models import DetectionEvent
from products.models import Product

from .models import BasketItem, BasketSession

CONFIDENCE_THRESHOLD = Decimal("0.75")


def generate_basket_code() -> str:
    next_id = BasketSession.objects.count() + 1
    while True:
        code = f"SB-{next_id:03d}"
        if not BasketSession.objects.filter(code=code).exists():
            return code
        next_id += 1


def create_basket_session(device_id: str) -> BasketSession:
    return BasketSession.objects.create(code=generate_basket_code(), device_id=device_id)


def recalculate_basket_total(basket: BasketSession) -> BasketSession:
    total = basket.items.aggregate(total=Sum("subtotal"))["total"] or Decimal("0.00")
    basket.total_amount = total
    basket.save(update_fields=["total_amount"])
    return basket


def _create_detection_event(
    basket: BasketSession,
    device_id: str,
    detected_label: str,
    confidence: Decimal,
    status: str,
    message: str,
) -> DetectionEvent:
    return DetectionEvent.objects.create(
        basket=basket,
        device_id=device_id,
        detected_label=detected_label,
        confidence=confidence,
        status=status,
        message=message,
    )


@transaction.atomic
def add_detection_to_basket(
    *,
    basket_code: str,
    device_id: str,
    detected_label: str,
    confidence: Decimal,
) -> tuple[BasketSession, DetectionEvent, BasketItem | None]:
    basket = BasketSession.objects.select_for_update().get(code=basket_code)

    if basket.status != BasketSession.Status.ACTIVE:
        event = _create_detection_event(
            basket,
            device_id,
            detected_label,
            confidence,
            DetectionEvent.Status.BASKET_CLOSED,
            "Le panier n'est plus actif.",
        )
        return basket, event, None

    product = Product.objects.filter(
        detection_label=detected_label,
        is_active=True,
    ).first()

    if product is None:
        event = _create_detection_event(
            basket,
            device_id,
            detected_label,
            confidence,
            DetectionEvent.Status.UNKNOWN_PRODUCT,
            "Aucun produit actif ne correspond a ce label IA.",
        )
        return basket, event, None

    if confidence < CONFIDENCE_THRESHOLD:
        event = _create_detection_event(
            basket,
            device_id,
            detected_label,
            confidence,
            DetectionEvent.Status.LOW_CONFIDENCE,
            "Confiance inferieure au seuil automatique.",
        )
        return basket, event, None

    item, created = BasketItem.objects.select_for_update().get_or_create(
        basket=basket,
        product=product,
        defaults={
            "quantity": 1,
            "unit_price": product.price,
            "last_confidence": confidence,
        },
    )
    if not created:
        item.quantity += 1
        item.last_confidence = confidence
    item.recalculate()
    item.save()
    basket = recalculate_basket_total(basket)

    event = _create_detection_event(
        basket,
        device_id,
        detected_label,
        confidence,
        DetectionEvent.Status.ACCEPTED,
        f"{product.name} ajoute au panier.",
    )
    return basket, event, item


@transaction.atomic
def remove_item_from_basket(*, basket_code: str, product_id: int) -> BasketSession:
    basket = BasketSession.objects.select_for_update().get(code=basket_code)
    if basket.status != BasketSession.Status.ACTIVE:
        raise ValidationError("Seul un panier actif peut etre modifie.")

    item = BasketItem.objects.select_for_update().filter(
        basket=basket,
        product_id=product_id,
    ).first()
    if item is None:
        raise ValidationError("Produit introuvable dans ce panier.")

    if item.quantity > 1:
        item.quantity -= 1
        item.recalculate()
        item.save()
    else:
        item.delete()

    return recalculate_basket_total(basket)


def _new_checkout_token() -> str:
    while True:
        token = token_urlsafe(24)
        if not BasketSession.objects.filter(checkout_token=token).exists():
            return token


def generate_qr_code(token: str, checkout_url: str) -> str:
    qr_dir = Path(settings.MEDIA_ROOT) / "qrcodes"
    qr_dir.mkdir(parents=True, exist_ok=True)
    qr_path = qr_dir / f"{token}.png"

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=4,
    )
    qr.add_data(checkout_url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    image.save(qr_path)
    return f"{settings.MEDIA_URL}qrcodes/{token}.png"


@transaction.atomic
def finish_basket(*, basket_code: str, checkout_url: str) -> BasketSession:
    basket = BasketSession.objects.select_for_update().prefetch_related("items").get(code=basket_code)
    if basket.status == BasketSession.Status.PAID:
        raise ValidationError("Ce panier est deja paye.")
    if basket.status == BasketSession.Status.CANCELLED:
        raise ValidationError("Ce panier est annule.")
    if not basket.items.exists():
        raise ValidationError("Impossible de terminer un panier vide.")

    if not basket.checkout_token:
        basket.checkout_token = _new_checkout_token()
    basket.status = BasketSession.Status.PENDING_CHECKOUT
    basket.finished_at = basket.finished_at or timezone.now()
    basket.save(update_fields=["checkout_token", "status", "finished_at"])

    checkout_url = checkout_url.replace("__TOKEN__", basket.checkout_token)
    generate_qr_code(basket.checkout_token, checkout_url)
    return basket
