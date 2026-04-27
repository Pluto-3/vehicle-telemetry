import strawberry
from typing import List
from django.db import IntegrityError, transaction

from api.types import TelemetryInput, IngestResult

def _run_pipeline(vehicle_id: str, inp: TelemetryInput):
    from ingestion.pipeline import run
    reading = {
        "timestamp": inp.timestamp.isoformat(),
        "speed": inp.speed,
        "fuel_level":inp.fuel_level,
        "latitude": inp.latitude,
        "longitude": inp.longitude,
    }
    run(vehicle_id, reading)

@strawberry.type
class Mutation:

    @strawberry.mutation
    def ingest_telemetry(self, input: TelemetryInput) -> IngestResult:
        from django.db import connection
        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO telemetry_telemetry
                    (vehicle_id, source_id, timestamp, speed, fuel_level, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (vehicle_id, source_id) DO NOTHING
                """,
                [str(input.vehicle_id), input.source_id, input.timestamp, input.speed, input.fuel_level, input.latitude, input.longitude],
            )
            created = cur.rowcount

        if created:
            _run_pipeline(str(input.vehicle_id), input)

        return IngestResult(
            success=True,
            created=created,
            message="inserted" if created else "duplicate skipped",
        )

    @strawberry.mutation
    def ingest_batch_telemetry(self, inputs: List[TelemetryInput]) -> IngestResult:
        from django.db import connection
        total_created = 0
        inserted_inputs = []

        with transaction.atomic():
            with connection.cursor() as cur:
                for inp in inputs:
                    cur.execute(
                        """
                        INSERT INTO telemetry_telemetry
                        (vehicle_id, source_id, timestamp, speed, fuel_level, latitude, longitude)
                        VALUES (%s, %s, %s, %s, %s, %s, %s,)
                        ON CONFLICT (vehicle_id, source_id) DO NOTHING
                        """,
                        [str(inp.vehicle_id), inp.source_id, inp.timestamp, inp.speed, inp.fuel_level, inp.latitude, inp.longitude],
                    )
                    if cur.rowcount:
                        total_created += 1
                        inserted_inputs.append(inp)

        for inp in inserted_inputs:
            _run_pipeline(str(inp.vehicle_id), inp)

        return IngestResult(
            success=True,
            created=total_created,
            message=f"{total_created}/{len(inputs)} inserted, {len(inputs)-total_created} duplicates skipped",
        )