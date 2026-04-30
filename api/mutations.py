import strawberry
from typing import List, Optional
from django.db import transaction
from api.types import TelemetryInput, IngestResult, DriverInput, DriverType, AssignmentInput, AssignmentType, VehicleType


def _run_pipeline(vehicle_id: str, inp):
    from ingestion.pipeline import run
    reading = {
        "timestamp": inp.timestamp.isoformat(),
        "speed": inp.speed,
        "fuel_level": inp.fuel_level,
        "latitude": inp.latitude,
        "longitude": inp.longitude,
    }
    run(vehicle_id, reading)


@strawberry.type
class Mutation:

    @strawberry.mutation
    def create_vehicle(self, plate_number: str, model: str) -> VehicleType:
        from vehicles.models import Vehicle
        v = Vehicle.objects.create(plate_number=plate_number, model=model)
        return VehicleType(id=v.id, plate_number=v.plate_number, model=v.model, created_at=v.created_at)

    @strawberry.mutation
    def create_driver(self, input: DriverInput) -> DriverType:
        from drivers.models import Driver
        d = Driver.objects.create(name=input.name, license_number=input.license_number)
        return DriverType(id=d.id, name=d.name, license_number=d.license_number)

    @strawberry.mutation
    def assign_driver(self, input: AssignmentInput) -> AssignmentType:
        from drivers.models import VehicleDriverAssignment
        from django.utils import timezone
        VehicleDriverAssignment.objects.filter(
            vehicle_id=input.vehicle_id, end_time__isnull=True
        ).update(end_time=timezone.now())
        a = VehicleDriverAssignment.objects.create(
            vehicle_id=input.vehicle_id,
            driver_id=input.driver_id,
            start_time=timezone.now(),
        )
        return AssignmentType(
            id=a.id, vehicle_id=a.vehicle_id, driver_id=a.driver_id,
            start_time=a.start_time, end_time=a.end_time,
        )

    @strawberry.mutation
    def ingest_telemetry(self, input: TelemetryInput) -> IngestResult:
        from django.db import connection
        from ingestion.rate_limit import check_rate_limit

        allowed, retry_after = check_rate_limit(str(input.vehicle_id), limit=60)
        if not allowed:
            return IngestResult(success=False, created=0, message=f"Rate limit exceeded. Retry after {retry_after}s")

        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO telemetry_telemetry
                    (vehicle_id, source_id, timestamp, speed, fuel_level, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (vehicle_id, source_id) DO NOTHING
                """,
                [str(input.vehicle_id), input.source_id, input.timestamp,
                 input.speed, input.fuel_level, input.latitude, input.longitude],
            )
            created = cur.rowcount
        if created:
            _run_pipeline(str(input.vehicle_id), input)
        return IngestResult(
            success=True, created=created,
            message="inserted" if created else "duplicate skipped",
        )

    @strawberry.mutation
    def ingest_batch_telemetry(self, inputs: List[TelemetryInput]) -> IngestResult:
        from django.db import connection
        from ingestion.rate_limit import check_rate_limit

        # Rate limit per unique vehicle in batch
        seen = set()
        for inp in inputs:
            vid = str(inp.vehicle_id)
            if vid not in seen:
                allowed, retry_after = check_rate_limit(vid, limit=20, window=60)
                if not allowed:
                    return IngestResult(success=False, created=0, message=f"Rate limit exceeded for {vid}. Retry after {retry_after}s")
                seen.add(vid)

        total_created = 0
        inserted_inputs = []
        with transaction.atomic():
            with connection.cursor() as cur:
                for inp in inputs:
                    cur.execute(
                        """
                        INSERT INTO telemetry_telemetry
                            (vehicle_id, source_id, timestamp, speed, fuel_level, latitude, longitude)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (vehicle_id, source_id) DO NOTHING
                        """,
                        [str(inp.vehicle_id), inp.source_id, inp.timestamp,
                         inp.speed, inp.fuel_level, inp.latitude, inp.longitude],
                    )
                    if cur.rowcount:
                        total_created += 1
                        inserted_inputs.append(inp)

        for inp in inserted_inputs:
            _run_pipeline(str(inp.vehicle_id), inp)

        return IngestResult(
            success=True, created=total_created,
            message=f"{total_created}/{len(inputs)} inserted, {len(inputs)-total_created} duplicates skipped",
        )