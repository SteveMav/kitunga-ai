from decimal import Decimal

from django.db import models
from django.utils import timezone

from products.models import Product


class BasketSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PENDING_CHECKOUT = "pending_checkout", "Pending checkout"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    code = models.CharField(max_length=24, unique=True)
    device_id = models.CharField(max_length=80)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    checkout_token = models.CharField(max_length=64, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["checkout_token"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} ({self.status})"

    def mark_paid(self) -> None:
        self.status = self.Status.PAID
        self.paid_at = timezone.now()


class BasketItem(models.Model):
    basket = models.ForeignKey(BasketSession, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="basket_items", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    last_confidence = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(fields=["basket", "product"], name="unique_product_per_basket"),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} x {self.quantity}"

    def recalculate(self) -> None:
        self.subtotal = self.unit_price * self.quantity
