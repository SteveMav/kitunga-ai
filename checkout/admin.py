from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("basket", "amount", "payment_method", "status", "validated_by", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("basket__code", "validated_by")
    readonly_fields = ("created_at",)
