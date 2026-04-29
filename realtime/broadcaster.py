"""
Called from ingestion pipeline after each insert.
Pushes to:
  - vehicle_{id} channel group
  - fleet_global channel group
  - Redis latest:{vehicle_id} cache key (for reconnecting clients)

All errors are caught and logged — never raises, never blocks ingestion.
"""
import json
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


def _send(group: str, payload: dict):
    try:
        async_to_sync(channel_layer.group_send)(group, payload)
    except Exception as e:
        logger.warning(f"Broadcast failed group={group}: {e}")


def broadcast_telemetry(vehicle_id: str, reading: dict):
    import redis as redis_lib
    from django.conf import settings

    payload = {
        "type": "telemetry.update",
        "vehicle_id": vehicle_id,
        "speed": reading.get("speed"),
        "fuel_level": reading.get("fuel_level"),
        "latitude": reading.get("latitude"),
        "longitude": reading.get("longitude"),
        "timestamp": reading.get("timestamp"),
    }

    # Cache latest state for reconnecting clients
    try:
        host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0][0]
        port = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0][1]
        r = redis_lib.Redis(host=host, port=port, decode_responses=True)
        r.setex(f"latest:{vehicle_id}", 3600, json.dumps(payload))
    except Exception as e:
        logger.warning(f"Redis cache latest state failed: {e}")

    # Broadcast to channel groups
    # Channels uses "." in type but handler method uses "_"
    ws_payload = {**payload, "type": "telemetry_update"}
    _send(f"vehicle_{vehicle_id}", ws_payload)
    _send("fleet_global", ws_payload)


def broadcast_event(vehicle_id: str, event):
    payload = {
        "type": "driving_event",
        "vehicle_id": vehicle_id,
        "event_type": event.event_type,
        "severity": event.severity,
        "timestamp": event.timestamp.isoformat(),
        "speed_before": event.speed_before,
        "speed_after": event.speed_after,
    }
    _send(f"vehicle_{vehicle_id}", payload)
    _send("fleet_global", payload)