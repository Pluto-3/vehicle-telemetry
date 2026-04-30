from django.contrib import admin
from .models import Telemetry


@admin.register(Telemetry)
class TelemetryAdmin(admin.ModelAdmin):
    list_display = ["vehicle", "timestamp", "speed", "fuel_level", "latitude", "longitude"]
    list_filter = ["vehicle"]
    search_fields = ["vehicle__plate_number", "source_id"]
    ordering = ["-timestamp"]
    readonly_fields = ["source_id", "vehicle", "timestamp"]
