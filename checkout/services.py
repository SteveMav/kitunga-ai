from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from baskets.models import BasketSession
from products.models import Product

from .models import Transaction


@transaction.atomic
def validate_checkout(
    *,
    token: str,
    validated_by: str = "demo_cashier",
    payment_method: str = "demo_cash",
) -> Transaction:
    basket = (
        BasketSession.objects.select_for_update()
        .prefetch_related("items__product")
        .get(checkout_token=token)
    )

    if basket.status != BasketSession.Status.PENDING_CHECKOUT:
        raise ValidationError("Le panier doit etre en attente de caisse.")
    if hasattr(basket, "transaction"):
        raise ValidationError("Une transaction existe deja pour ce panier.")

    for item in basket.items.all():
        product = Product.objects.select_for_update().get(pk=item.product_id)
        if product.stock_quantity < item.quantity:
            raise ValidationError(f"Stock insuffisant pour {product.name}.")

    transaction_record = Transaction.objects.create(
        basket=basket,
        amount=basket.total_amount,
        payment_method=payment_method,
        status=Transaction.Status.PAID,
        validated_by=validated_by,
    )

    for item in basket.items.all():
        Product.objects.filter(pk=item.product_id).update(
            stock_quantity=F("stock_quantity") - item.quantity,
        )

    basket.mark_paid()
    basket.save(update_fields=["status", "paid_at"])
    return transaction_record
