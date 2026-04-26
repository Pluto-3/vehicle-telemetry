import uuid
from datetime import datetime, timezone
from django.test import TestCase
from vehicles.models import Vehicle
from telemetry.models import Telemetry
from django.db import IntegrityError


def make_vehicle():
    return Vehicle.objects.create(plate_number=f"TST-{uuid.uuid4().hex[:6].upper()}", model="TestCar")


def make_telemetry(vehicle, source_id, speed=60.0):
    return Telemetry.objects.create(
        vehicle=vehicle,
        source_id=source_id,
        timestamp=datetime.now(timezone.utc),
        speed=speed,
        fuel_level=80.0,
        latitude=6.5244,
        longitude=3.3792,
    )


class IdempotencyTest(TestCase):

    def test_duplicate_source_id_raises(self):
        v = make_vehicle()
        make_telemetry(v, "src-001")
        with self.assertRaises(IntegrityError):
            make_telemetry(v, "src-001")

    def test_same_source_id_different_vehicle_ok(self):
        v1 = make_vehicle()
        v2 = make_vehicle()
        make_telemetry(v1, "src-001")
        # Should not raise — different vehicle
        make_telemetry(v2, "src-001")
        self.assertEqual(Telemetry.objects.count(), 2)

    def test_different_source_ids_both_inserted(self):
        v = make_vehicle()
        make_telemetry(v, "src-001")
        make_telemetry(v, "src-002")
        self.assertEqual(Telemetry.objects.filter(vehicle=v).count(), 2)
