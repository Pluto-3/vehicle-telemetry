from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["plate_number", "model", "created_at"]
    search_fields = ["plate_number", "model"]
    ordering = ["-created_at"]
