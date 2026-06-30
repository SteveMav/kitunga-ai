from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "detection_label",
        "price",
        "currency",
        "stock_quantity",
        "is_active",
    )
    list_filter = ("category", "currency", "is_active")
    search_fields = ("name", "category", "detection_label")
    ordering = ("category", "name")
