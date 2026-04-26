import strawberry
from typing import List
from django.db import IntegrityError, transaction

from api.types import TelemetryInput, IngestResult


def _build_telemetry_obj(inp: TelemetryInput):
    from telemetry.models import Telemetry
    return Telemetry(
        vehicle_id=inp.vehicle_id,
        source_id=inp.source_id,
        timestamp=inp.timestamp,
        speed=inp.speed,
        fuel_level=inp.fuel_level,
        latitude=inp.latitude,
        longitude=inp.longitude,
    )


@strawberry.type
class Mutation:

    @strawberry.mutation
    def ingest_telemetry(self, input: TelemetryInput) -> IngestResult:
        from telemetry.models import Telemetry
        from django.db import connection

        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO telemetry_telemetry
                    (vehicle_id, source_id, timestamp, speed, fuel_level, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (vehicle_id, source_id) DO NOTHING
                """,
                [
                    str(input.vehicle_id), input.source_id, input.timestamp,
                    input.speed, input.fuel_level, input.latitude, input.longitude,
                ],
            )
            created = cur.rowcount  # 1 = inserted, 0 = duplicate skipped

        return IngestResult(
            success=True,
            created=created,
            message="inserted" if created else "duplicate skipped",
        )

    @strawberry.mutation
    def ingest_batch_telemetry(self, inputs: List[TelemetryInput]) -> IngestResult:
        """
        Entire batch in one transaction.
        Duplicates silently skipped via ON CONFLICT DO NOTHING.
        On any non-conflict DB error the whole batch rolls back — caller retries safely.
        """
        from django.db import connection

        total_created = 0
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
                        [
                            str(inp.vehicle_id), inp.source_id, inp.timestamp,
                            inp.speed, inp.fuel_level, inp.latitude, inp.longitude,
                        ],
                    )
                    total_created += cur.rowcount

        return IngestResult(
            success=True,
            created=total_created,
            message=f"{total_created}/{len(inputs)} inserted, {len(inputs)-total_created} duplicates skipped",
        )
