import json
from datetime import datetime
import redis as redis_lib
from django.conf import settings

WINDOW_SIZE = 10
GAP_THRESHOLD_SEC = 10

def _get_redis():
    host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0][0]
    port = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0][1]
    return redis_lib.Redis(host=host, port=port, decode_responses=True)

def _window_key(vehicle_id: str) -> str:
    return f"telwin:{vehicle_id}"

def get_window(vehicle_id: str) -> list:
    r = _get_redis()
    raw = r.lrange(_window_key(vehicle_id), 0, -1)
    return [json.loads(x) for x in raw]

def push_reading(vehicle_id: str, reading: dict) -> list:
    r = _get_redis()
    key = _window_key(vehicle_id)
    window = get_window(vehicle_id)

    if window:
        last_ts = datetime.fromisoformat(window[-1]["timestamp"])
        curr_ts = datetime.fromisoformat(reading["timestamp"])
        gap = (curr_ts - last_ts).total_seconds()
        if gap > GAP_THRESHOLD_SEC:
            r.delete(key)

    r.rpush(key, json.dumps(reading))
    r.ltrim(key, -WINDOW_SIZE, -1)
    r.expire(key, 3600)
    return get_window(vehicle_id)