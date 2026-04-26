from django.contrib import admin
from .models import DrivingEvent

@admin.register(DrivingEvent)
class DrivingEventAdmin(admin.ModelAdmin):
    list_display = ["vehicle", "event_type", "severity", "timestamp"]
    list_filter = ["event_type", "vehicle"]