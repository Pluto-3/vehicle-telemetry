from datetime import datetime
from events.models import DrivingEvent
from events.detector import DetectedEvent

def resolve_driver(vehicle_id, event_ts):
    from drivers.models import VehicleDriverAssignment
    assignment = (
        VehicleDriverAssignment.objects
        .filter(vehicle_id=vehicle_id, start_time__lte=event_ts)
        .filter(end_time__isnull=True) |
        VehicleDriverAssignment.objects
        .filter(vehicle_id=vehicle_id, start_time__lte=event_ts, end_time__gte=event_ts)
    ).order_by("-start_time").first()
    return assignment.driver_id if assignment else None

def save_events(vehicle_id, detected: list[DetectedEvent]) -> list[DrivingEvent]:
    saved = []
    for e in detected:
        driver_id = resolve_driver(vehicle_id, e.timestamp)
        obj = DrivingEvent.objects.create(
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            event_type=e.event_type,
            severity=e.severity,
            timestamp=e.timestamp,
            speed_before=e.speed_before,
            speed_after=e.speed_after,
        )
        saved.append(obj)
    return saved
