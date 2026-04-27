"""
ScoringService
- 30-day rolling window
- Exponential time decay: penalty × e^(-λ × days_ago), λ=0.05
- Normalized per km driven (estimated from telemetry)
- Score = 100 - sum(decayed penalties), floor 0
- Snapshots written on demand; call compute_and_save() every 6h via cron/management cmd
"""


import math
from datetime import datetime, timedelta, timezone

DECAY_LAMBDA = 0.05
WINDOW_DAYS = 30
BASE_SCORE = 100.0
PENALTIES = {
    "HARSH_BRAKE": 5.0,
    "RAPID_ACCEL": 3.0,
    "OVERSPEED": 2.0,
}
KM_NORMALIZATION_BASELINE = 100.0

def _decayed_penalty(event, now: datetime) -> float:
    base = PENALTIES.get(event.event_type, 2.0) * event.severity
    days_ago = (now - event.timestamp.replace(tzinfo=timezone.utc)).total_seconds()  / 86400
    return base * math.exp(-DECAY_LAMBDA * days_ago)

def compute_score(driver_id) -> dict:
    from events.models import DrivingEvent
    from telemetry.models import Telemetry
    from drivers.models import VehicleDriverAssignment

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=WINDOW_DAYS)

    events = DrivingEvent.objects.filter(
        driver_id=driver_id,
        timestamp__gte=window_start,
    )

    total_penalty = sum(_decayed_penalty(e, now) for e in events)

    # Estimate km driven: fetch telemetry data for all vehicles this driver used
    assignments = VehicleDriverAssignment.objects.filter(
        driver_id=driver_id,
        start_time__gte=window_start,
    )
    km_driven = 0.0
    for a in assignments:
        end = a.end_time or now
        readings = (
            Telemetry.objects
            .filter(vehicle_id=a.vehicle_id, timestamp__gte=a.start_time, timestamp__lte=end)
            .order_by("timestamp")
        )
        prev_ts = None
        for speed, ts in readings:
            if prev_ts:
                hours = (ts.replace(tzinfo=timezone.utc) - prev_ts).total_seconds() / 3600
                km_driven += speed * hours
            prev_ts = ts.replace(tzinfo=timezone.utc)

    # Normalize scale penalty by km ratio (more km = dilute penalty, only fair)
    if km_driven > 0:
        scale = KM_NORMALIZATION_BASELINE / km_driven
        total_penalty *= scale

    score = max(0.0, BASE_SCORE - total_penalty)
    return {"score": round(score, 2), "km_driven": round(km_driven, 2)}

def compute_and_save(driver_id):
    from scoring.models import DriverScore
    result = compute_score(driver_id)
    DriverScore.objects.create(
        driver_id=driver_id,
        score=result["score"],
        km_driven=result["km_driven"],
        window_days=WINDOW_DAYS,
    )
    return result