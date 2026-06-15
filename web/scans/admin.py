from django.contrib import admin

from .models import Scan


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "predicted_class",
        "created_at",
        "processing_time_seconds",
    )
    list_filter = ("status", "predicted_class", "created_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = (
        "created_at",
        "processing_time_seconds",
        "confidence_ad",
        "confidence_pd",
        "confidence_control",
        "error_message",
    )
