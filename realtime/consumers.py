import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
import redis.asyncio as aioredis
from django.conf import settings

logger = logging.getLogger(__name__)


def _redis_url() -> str:
    host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0][0]
    port = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0][1]
    return f"redis://{host}:{port}"


class VehicleConsumer(AsyncWebsocketConsumer):
    """
    ws://host/ws/vehicle/<vehicle_id>/
    Receives real-time telemetry + events for a single vehicle.
    """

    async def connect(self):
        self.vehicle_id = self.scope["url_route"]["kwargs"]["vehicle_id"]
        self.group_name = f"vehicle_{self.vehicle_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send latest cached state immediately on connect
        await self._send_latest_state()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # ── Handlers for messages broadcast from ingestion pipeline ──

    async def telemetry_update(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            logger.warning(f"WS send failed (telemetry) vehicle={self.vehicle_id}: {e}")

    async def driving_event(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            logger.warning(f"WS send failed (event) vehicle={self.vehicle_id}: {e}")

    async def _send_latest_state(self):
        try:
            r = aioredis.from_url(_redis_url(), decode_responses=True)
            raw = await r.get(f"latest:{self.vehicle_id}")
            await r.aclose()
            if raw:
                await self.send(text_data=raw)
        except Exception as e:
            logger.warning(f"Failed to send latest state vehicle={self.vehicle_id}: {e}")


class FleetConsumer(AsyncWebsocketConsumer):
    """
    ws://host/ws/fleet/
    Receives updates for all vehicles.
    """

    async def connect(self):
        self.group_name = "fleet_global"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def telemetry_update(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            logger.warning(f"WS send failed (fleet telemetry): {e}")

    async def driving_event(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            logger.warning(f"WS send failed (fleet event): {e}")