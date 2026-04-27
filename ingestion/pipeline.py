from telemetry.services import push_reading
from events.detector import detect
from events.services import save_events

def run(vehicle_id: str, reading: dict):
    window = push_reading(vehicle_id, reading)
    detected = detect(window)
    if detected:
        save_events(vehicle_id, detected)
    return detected