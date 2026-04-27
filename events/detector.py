"""
EventDetector
Stateless — takes a window (list of readings, oldest first) and emits events.

Thresholds:
  Harsh brake:    speed drop  > 20 km/h over <=3s, confirmed by 2+ readings
  Rapid accel:    speed gain  > 25 km/h over <=3s, confirmed by 2+ readings
  Overspeed:      speed       > 100 km/h for 2+ consecutive readings

Severity (1-5):
  Computed from magnitude of delta relative to threshold step.
"""


from dataclasses import dataclass
from datetime import datetime
from typing import Optional

BRAKE_THRESHOLD = 20
ACCEL_THRESHOLD = 25
OVERSPEED_LIMIT = 100
WINDOW_SEC = 3
NOISE_MIN = 2

@dataclass
class DetectedEvent:
    event_type: str
    severity: int
    timestamp: datetime
    speed_before: Optional[float]
    speed_after: Optional[float]

def _severity(delta: float, threshold: float, step: float = 5.0) -> int:
    """ Clamp (delta - threshold) / step into 1-5."""
    return max(1, min(5, int((delta - threshold) / step) + 1))

def _ts(reading: dict) -> datetime:
    return datetime.fromisoformat(reading["timestamp"])

def detect(window: list[dict]) -> list[DetectedEvent]:
    if len(window) < NOISE_MIN:
        return []
    
    events = []
    latest = window[-1]
    latest_speed = latest["speed"]
    latest_ts = _ts(latest)

    recent = [
        r for r in window
        if abs((_ts(latest) - _ts(r)).total_seconds()) <= WINDOW_SEC
    ]

    if len(recent) < NOISE_MIN:
        return []
    
    earliest_recent = recent[0]
    earliest_speed = earliest_recent["speed"]
    delta = earliest_speed - latest_speed # +ve = speed dropped

    # Harsh braking
    if delta >= BRAKE_THRESHOLD:
        speeds = [r["speed"] for r in recent]
        if speeds == sorted(speeds, reverse=True):
            events.append(DetectedEvent(
                event_type="HARSH_BRAKE",
                severity=_severity(delta, BRAKE_THRESHOLD),
                timestamp=latest_ts,
                speed_before=earliest_speed,
                speed_after=latest_speed,
            )) 

    # Rapid acceleration
    elif -delta >= ACCEL_THRESHOLD:
        speeds = [r["speed"] for r in recent]
        if speeds == sorted(speeds):
            events.append(DetectedEvent(
                event_type="RAPID_ACCEL",
                severity=_severity(-delta, ACCEL_THRESHOLD),
                timestamp=latest_ts,
                speed_before=earliest_speed,
                speed_after=latest_speed,
            ))

    # Overspeed
    last_n_speeds = [r["speed"] for r in window[-NOISE_MIN:]]
    if all(s > OVERSPEED_LIMIT for s in last_n_speeds):
        events.append(DetectedEvent(
            event_type="OVERSPEED",
            severity=_severity(latest_speed, OVERSPEED_LIMIT, step=10.0),
            timestamp=latest_ts,
            speed_before=None,
            speed_after=latest_speed,
        ))

    return events