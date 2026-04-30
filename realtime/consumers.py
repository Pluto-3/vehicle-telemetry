import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
import redis.asyncio as aioredis
from django.conf import settings

logger = logging.getLogger(__name__)


def _redis_url():
    host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0][0]
    port = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0][1]
    return f"redis://{host}:{port}"


def _validate_key(key: str) -> bool:
    if not key or not key.startswith("tlm_"):
        return False
    from ingestion.models import APIKey
    return APIKey.objects.filter(key=key, is_active=True).exists()


class VehicleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Auth check — skip in DEBUG
        if not settings.DEBUG:
            api_key = self.scope["query_string"].decode()
            api_key = dict(x.split("=") for x in api_key.split("&") if "=" in x).get("api_key", "")
            from asgiref.sync import sync_to_async
            valid = await sync_to_async(_validate_key)(api_key)
            if not valid:
                await self.close(code=4401)
                return

        self.vehicle_id = self.scope["url_route"]["kwargs"]["vehicle_id"]
        self.group_name = f"vehicle_{self.vehicle_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self._send_latest_state()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def telemetry_update(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            logger.warning(f"WS send failed vehicle={self.vehicle_id}: {e}")

    async def driving_event(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            logger.warning(f"WS event send failed vehicle={self.vehicle_id}: {e}")

    async def _send_latest_state(self):
        try:
            r = aioredis.from_url(_redis_url(), decode_responses=True)
            raw = await r.get(f"latest:{self.vehicle_id}")
            await r.aclose()
            if raw:
                await self.send(text_data=raw)
        except Exception as e:
            logger.warning(f"Latest state fetch failed: {e}")


class FleetConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not settings.DEBUG:
            api_key = self.scope["query_string"].decode()
            api_key = dict(x.split("=") for x in api_key.split("&") if "=" in x).get("api_key", "")
            from asgiref.sync import sync_to_async
            valid = await sync_to_async(_validate_key)(api_key)
            if not valid:
                await self.close(code=4401)
                return

        self.group_name = "fleet_global"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def telemetry_update(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            logger.warning(f"WS fleet send failed: {e}")

    async def driving_event(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            logger.warning(f"WS fleet event failed: {e}")
