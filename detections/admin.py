from django.contrib import admin

from .models import DetectionEvent


@admin.register(DetectionEvent)
class DetectionEventAdmin(admin.ModelAdmin):
    list_display = ("basket", "device_id", "detected_label", "confidence", "status", "created_at")
    list_filter = ("status", "created_at", "device_id")
    search_fields = ("basket__code", "device_id", "detected_label", "message")
    readonly_fields = ("created_at",)
