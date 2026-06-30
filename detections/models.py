from django.db import models

from baskets.models import BasketSession


class DetectionEvent(models.Model):
    class Status(models.TextChoices):
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        NEEDS_CONFIRMATION = "needs_confirmation", "Needs confirmation"
        UNKNOWN_PRODUCT = "unknown_product", "Unknown product"
        LOW_CONFIDENCE = "low_confidence", "Low confidence"
        BASKET_CLOSED = "basket_closed", "Basket closed"

    basket = models.ForeignKey(BasketSession, related_name="detections", on_delete=models.CASCADE)
    device_id = models.CharField(max_length=80)
    detected_label = models.CharField(max_length=120)
    confidence = models.DecimalField(max_digits=4, decimal_places=2)
    status = models.CharField(max_length=32, choices=Status.choices)
    message = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["detected_label"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.detected_label} ({self.confidence}) - {self.status}"
