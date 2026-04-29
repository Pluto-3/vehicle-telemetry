import argparse
import logging
import threading
import time
import os
import sys
import django

# Bootstrap Django so we can query vehicle UUIDs
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from simulator.vehicle import VehicleSimulator
from simulator.sender import send_batch, BATCH_SIZE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_or_create_vehicles(n: int) -> list:
    from vehicles.models import Vehicle
    vehicles = list(Vehicle.objects.all()[:n])
    while len(vehicles) < n:
        idx = len(vehicles) + 1
        v = Vehicle.objects.create(
            plate_number=f"SIM-{idx:03d}",
            model=f"Simulator Vehicle {idx}",
        )
        vehicles.append(v)
        logger.info(f"Created vehicle {v.plate_number} ({v.id})")
    return vehicles


def simulate_vehicle(vehicle_id: str, interval: float, duration: float, stop_event: threading.Event):
    sim = VehicleSimulator(vehicle_id)
    batch = []
    start = time.time()
    logger.info(f"Vehicle {vehicle_id[:8]}... started on route '{sim.route_name}'")

    while not stop_event.is_set():
        if duration > 0 and (time.time() - start) >= duration:
            break

        reading = sim.next_reading()
        batch.append(reading)

        if len(batch) >= BATCH_SIZE:
            result = send_batch(batch)
            if result:
                logger.info(
                    f"Vehicle {vehicle_id[:8]}... "
                    f"speed={reading['speed']} km/h "
                    f"fuel={reading['fuelLevel']}% "
                    f"→ {result['message']}"
                )
            batch = []

        time.sleep(interval)

    # Flush remaining
    if batch:
        send_batch(batch)
    logger.info(f"Vehicle {vehicle_id[:8]}... stopped.")


def main():
    parser = argparse.ArgumentParser(description="Vehicle telemetry simulator")
    parser.add_argument("--vehicles", type=int, default=3)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--duration", type=float, default=0)
    args = parser.parse_args()

    vehicles = get_or_create_vehicles(args.vehicles)
    stop_event = threading.Event()
    threads = []

    for v in vehicles:
        t = threading.Thread(
            target=simulate_vehicle,
            args=(str(v.id), args.interval, args.duration, stop_event),
            name=f"sim-{v.plate_number}",
            daemon=True,
        )
        threads.append(t)
        t.start()

    logger.info(f"Simulating {args.vehicles} vehicle(s). Press Ctrl+C to stop.")
    try:
        while any(t.is_alive() for t in threads):
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Stopping simulation...")
        stop_event.set()
        for t in threads:
            t.join(timeout=5)
    logger.info("Simulation ended.")


if __name__ == "__main__":
    main()