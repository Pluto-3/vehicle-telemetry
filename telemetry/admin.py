from django.contrib import admin
from .models import Telemetry

@admin.register(Telemetry)
class TelemetryAdmin(admin.ModelAdmin):
    list_display = ["vehicle", "timestamp", "speed", "fuel_level", "source_id"]
    list_filter = ["vehicle"]
    ordering = ["timestamp"]