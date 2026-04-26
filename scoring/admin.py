from django.contrib import admin
from .models import DriverScore

@admin.register(DriverScore)
class DriverScoreAdmin(admin.ModelAdmin):
    list_display = ["driver", "score", "km_driven", "calculated_at"]