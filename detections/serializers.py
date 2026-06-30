from rest_framework import serializers

from .models import DetectionEvent


class DetectionEventSerializer(serializers.ModelSerializer):
    basket_code = serializers.CharField(source="basket.code", read_only=True)

    class Meta:
        model = DetectionEvent
        fields = [
            "id",
            "basket_code",
            "device_id",
            "detected_label",
            "confidence",
            "status",
            "message",
            "created_at",
        ]
