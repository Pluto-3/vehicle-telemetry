from telemetry.services import push_reading
from events.detector import detect
from events.services import save_events
from realtime.broadcaster import broadcast_telemetry, broadcast_event

def run(vehicle_id: str, reading: dict):
    window = push_reading(vehicle_id, reading)
    detected = detect(window)

    if detected:
        save_events(vehicle_id, detected)
    
    # broadcast
    broadcast_telemetry(vehicle_id, reading)
    for event in detected:
        broadcast_event(vehicle_id, event)
    
    return detected