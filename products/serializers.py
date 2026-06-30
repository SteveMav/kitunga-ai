from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "detection_label",
            "price",
            "currency",
            "stock_quantity",
            "image",
            "is_active",
            "created_at",
            "updated_at",
        ]
