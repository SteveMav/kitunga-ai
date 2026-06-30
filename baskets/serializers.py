from rest_framework import serializers

from .models import BasketItem, BasketSession


class BasketItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source="product.id", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    category = serializers.CharField(source="product.category", read_only=True)
    currency = serializers.CharField(source="product.currency", read_only=True)
    image = serializers.ImageField(source="product.image", read_only=True)

    class Meta:
        model = BasketItem
        fields = [
            "product_id",
            "product_name",
            "category",
            "quantity",
            "unit_price",
            "subtotal",
            "last_confidence",
            "currency",
            "image",
        ]


class BasketSessionSerializer(serializers.ModelSerializer):
    items = BasketItemSerializer(many=True, read_only=True)
    checkout_url = serializers.SerializerMethodField()
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = BasketSession
        fields = [
            "code",
            "device_id",
            "status",
            "total_amount",
            "checkout_token",
            "checkout_url",
            "qr_code_url",
            "created_at",
            "finished_at",
            "paid_at",
            "items",
        ]

    def get_checkout_url(self, basket: BasketSession) -> str | None:
        if not basket.checkout_token:
            return None
        request = self.context.get("request")
        path = f"/checkout/t/{basket.checkout_token}/"
        return request.build_absolute_uri(path) if request else path

    def get_qr_code_url(self, basket: BasketSession) -> str | None:
        if not basket.checkout_token:
            return None
        request = self.context.get("request")
        path = f"/media/qrcodes/{basket.checkout_token}.png"
        return request.build_absolute_uri(path) if request else path


class StartBasketSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=80, default="KITUNGA-PI-001")


class AddDetectionSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=80)
    detected_label = serializers.CharField(max_length=120)
    confidence = serializers.DecimalField(max_digits=4, decimal_places=2, min_value=0, max_value=1)


class RemoveItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
