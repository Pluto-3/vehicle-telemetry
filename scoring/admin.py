from django.contrib import admin
from .models import DriverScore

@admin.register(DriverScore)
class DriverScoreAdmin(admin.ModelAdmin):
    list_display = ["driver", "score", "km_driven", "window_Days", "calculated_at"]
    list_filter = ["window_Days"]
    search_fields = ["driver__name"]
    ordering = ["-calculated_at"]
    readonly_fields = ["calculated_at"]