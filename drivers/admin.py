from django.contrib import admin
from .models import Driver, VehicleDriverAssignment


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ["name", "license_number", "created_at"]
    search_fields = ["name", "license_number"]


@admin.register(VehicleDriverAssignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["driver", "vehicle", "start_time", "end_time"]
    list_filter = ["vehicle"]
    ordering = ["-start_time"]
