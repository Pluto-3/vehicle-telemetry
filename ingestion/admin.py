from django.contrib import admin
from .models import APIKey

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ["name", "key", "is_active", "created_at", "last_used"]
    readonly_fields = ["key", "created_at", "last_used"]
    list_filter = ["is_active"]