from django.contrib import admin

from .models import BasketItem, BasketSession


class BasketItemInline(admin.TabularInline):
    model = BasketItem
    extra = 0
    readonly_fields = ("subtotal", "created_at", "updated_at")


@admin.register(BasketSession)
class BasketSessionAdmin(admin.ModelAdmin):
    list_display = ("code", "device_id", "status", "total_amount", "created_at", "finished_at", "paid_at")
    list_filter = ("status", "created_at")
    search_fields = ("code", "device_id", "checkout_token")
    readonly_fields = ("created_at", "finished_at", "paid_at")
    inlines = [BasketItemInline]


@admin.register(BasketItem)
class BasketItemAdmin(admin.ModelAdmin):
    list_display = ("basket", "product", "quantity", "unit_price", "subtotal", "last_confidence")
    list_filter = ("basket__status", "product__category")
    search_fields = ("basket__code", "product__name", "product__detection_label")
