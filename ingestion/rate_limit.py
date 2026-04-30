"""
Redis-based rate limiter for telemetry ingestion.
Uses sliding window counter per vehicle_id.

Limits:
  - Single ingest:  60 requests/min per vehicle
  - Batch ingest:   20 requests/min per vehicle

Returns (allowed: bool, retry_after: int seconds)
"""
import time
import redis as redis_lib
from django.conf import settings


def _get_redis():
    host = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0][0]
    port = settings.CHANNEL_LAYERS["default"]["CONFIG"]["hosts"][0][1]
    return redis_lib.Redis(host=host, port=port, decode_responses=True)


def check_rate_limit(vehicle_id: str, limit: int = 60, window: int = 60) -> tuple[bool, int]:
    """
    Sliding window rate limit.
    Returns (allowed, retry_after_seconds).
    """
    try:
        r = _get_redis()
        key = f"ratelimit:{vehicle_id}:{window}"
        now = time.time()
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, now - window)   # remove old entries
        pipe.zadd(key, {str(now): now})                # add current request
        pipe.zcard(key)                                # count in window
        pipe.expire(key, window)
        _, _, count, _ = pipe.execute()

        if count > limit:
            return False, window
        return True, 0
    except Exception:
        # Redis down — fail open (don't block ingestion)
        return True, 0
