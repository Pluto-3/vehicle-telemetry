import random
import math
from datetime import datetime, timezone, timedelta
from simulator.routes import ROUTES, ROUTE_NAMES

class VehicleSimulator:

    BRAKE_PROB = 0.015      # 1.5% chance of harsh braking seq
    ACCEL_PROB = 0.010      # 1.0% chance of rapid acceleration seq
    OVER_PROB = 0.008       # 0.8% chance of overspeed burst

    SPEED_LIMIT = 80.0      # norm cruising cap
    OVERSPEED = 115.0       # overspeed burst target
    NOISE = 5.0             # random noise

    def __init__(self, vehicle_id: str, route_name: str = None):
        self.vehicle_id = str(vehicle_id)
        self.route_name = route_name or random.choice(ROUTE_NAMES)
        self.waypoints = ROUTES[self.route_name]
        self.wp_index = 0
        self.speed = random.uniform(40, 70)
        self.fuel = random.uniform(60, 100)
        self.timestamp = datetime.now(timezone.utc)
        self.seq = 0

        self._event_seq = [] # queued speed targets for cur events

    def _interpolate_position(self):
        wp = self.waypoints[self.wp_index % len(self.waypoints)]
        next_wp = self.waypoints[(self.wp_index + 1) % len(self.waypoints)]

        if self.seq % 10 == 0:
            self.wp_index = (self.wp_index + 1) % len(self.waypoints)

        t = (self.seq % 10) / 10.0
        lat = wp[0] + t * (next_wp[0] - wp[0])
        lng = wp[1] + t * (next_wp[1] - wp[1])
        return lat, lng
    
    def _next_speed(self) -> float:
        if self._event_seq:
            return self._event_seq.pop(0)

        # Inject events probabilistically
        r = random.random()
        if r < self.BRAKE_PROB:
            # Harsh brake: drop 25-40 km/h over 2 readings
            drop = random.uniform(25, 40)
            self._event_seq = [
                max(10, self.speed - drop * 0.5),
                max(10, self.speed - drop),
            ]
        elif r < self.BRAKE_PROB + self.ACCEL_PROB:
            # Rapid accel: gain 28-40 km/h over 2 readings
            gain = random.uniform(28, 40)
            self._event_seq = [
                min(self.SPEED_LIMIT, self.speed + gain * 0.5),
                min(self.SPEED_LIMIT, self.speed + gain),
            ]
        elif r < self.BRAKE_PROB + self.ACCEL_PROB + self.OVER_PROB:
            # Overspeed burst: 3 readings above limit
            burst = random.uniform(self.OVERSPEED, self.OVERSPEED + 20)
            self._event_seq = [burst, burst + random.uniform(-5, 5), burst - 10]

        # Normal: drift toward cruise speed with noise
        target = random.uniform(50, self.SPEED_LIMIT)
        drift = (target - self.speed) * 0.2
        return max(0, self.speed + drift + random.uniform(-self.NOISE, self.NOISE))

    def _fuel_consumption(self, speed: float, elapsed_sec: float) -> float:
        """Simple fuel model: higher speed = more consumption."""
        hours = elapsed_sec / 3600
        consumption = (speed / 100) * 8 * hours   # ~8L/100km baseline
        return max(0, self.fuel - consumption)

    def next_reading(self) -> dict:
        self.seq += 1
        self.timestamp += timedelta(seconds=1)
        self.speed = self._next_speed()
        self.fuel = self._fuel_consumption(self.speed, 1)
        lat, lng = self._interpolate_position()

        source_id = f"{self.vehicle_id}:{int(self.timestamp.timestamp() * 1000)}:{self.seq}"

        return {
            "vehicleId": self.vehicle_id,
            "sourceId": source_id,
            "timestamp": self.timestamp.isoformat(),
            "speed": round(self.speed, 2),
            "fuelLevel": round(self.fuel, 2),
            "latitude": round(lat, 6),
            "longitude": round(lng, 6),
        }