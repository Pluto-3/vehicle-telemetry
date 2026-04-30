"""
API key authentication for GraphQL and WebSocket endpoints.

GraphQL: pass key in header  →  X-API-Key: tlm_xxxxx
WebSocket: pass key in query →  ws://host/ws/vehicle/<id>/?api_key=tlm_xxxxx
"""
from django.utils import timezone
from ingestion.models import APIKey


def validate_api_key(key: str) -> bool:
    if not key or not key.startswith("tlm_"):
        return False
    try:
        api_key = APIKey.objects.get(key=key, is_active=True)
        api_key.last_used = timezone.now()
        api_key.save(update_fields=["last_used"])
        return True
    except APIKey.DoesNotExist:
        return False
