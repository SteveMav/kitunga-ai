from django.db import models

from baskets.models import BasketSession


class Transaction(models.Model):
    class Status(models.TextChoices):
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    basket = models.OneToOneField(BasketSession, related_name="transaction", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=40, default="demo_cash")
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PAID)
    validated_by = models.CharField(max_length=120, default="demo_cashier")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.basket.code} - {self.amount}"
