import strawberry
from typing import Optional, List
from datetime import datetime
import uuid
from api.types import VehicleType, TelemetryType, DriverScoreType, DrivingEventType, DriverType


@strawberry.type
class Query:

    @strawberry.field
    def get_vehicle(self, id: uuid.UUID) -> Optional[VehicleType]:
        from vehicles.models import Vehicle
        try:
            v = Vehicle.objects.get(pk=id)
            return VehicleType(id=v.id, plate_number=v.plate_number, model=v.model, created_at=v.created_at)
        except Vehicle.DoesNotExist:
            return None

    @strawberry.field
    def list_vehicles(self) -> List[VehicleType]:
        from vehicles.models import Vehicle
        return [
            VehicleType(id=v.id, plate_number=v.plate_number, model=v.model, created_at=v.created_at)
            for v in Vehicle.objects.all()
        ]

    @strawberry.field
    def list_drivers(self) -> List[DriverType]:
        from drivers.models import Driver
        return [
            DriverType(id=d.id, name=d.name, license_number=d.license_number)
            for d in Driver.objects.all()
        ]

    @strawberry.field
    def get_vehicle_telemetry(
        self, vehicle_id: uuid.UUID,
        from_dt: Optional[datetime] = None,
        to_dt: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[TelemetryType]:
        from telemetry.models import Telemetry
        qs = Telemetry.objects.filter(vehicle_id=vehicle_id)
        if from_dt:
            qs = qs.filter(timestamp__gte=from_dt)
        if to_dt:
            qs = qs.filter(timestamp__lte=to_dt)
        return [
            TelemetryType(
                id=t.id, vehicle_id=t.vehicle_id, timestamp=t.timestamp,
                speed=t.speed, fuel_level=t.fuel_level,
                latitude=t.latitude, longitude=t.longitude, source_id=t.source_id,
            )
            for t in qs.order_by("-timestamp")[:limit]
        ]

    @strawberry.field
    def get_driver_score(self, driver_id: uuid.UUID) -> Optional[DriverScoreType]:
        from scoring.models import DriverScore
        s = DriverScore.objects.filter(driver_id=driver_id).order_by("-calculated_at").first()
        if not s:
            return None
        return DriverScoreType(driver_id=s.driver_id, score=s.score, km_driven=s.km_driven, calculated_at=s.calculated_at)

    @strawberry.field
    def get_vehicle_events(
        self, vehicle_id: uuid.UUID,
        from_dt: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[DrivingEventType]:
        from events.models import DrivingEvent
        qs = DrivingEvent.objects.filter(vehicle_id=vehicle_id)
        if from_dt:
            qs = qs.filter(timestamp__gte=from_dt)
        return [
            DrivingEventType(
                id=e.id, vehicle_id=e.vehicle_id, event_type=e.event_type,
                severity=e.severity, timestamp=e.timestamp,
                speed_before=e.speed_before, speed_after=e.speed_after,
            )
            for e in qs.order_by("-timestamp")[:limit]
        ]

    @strawberry.field
    def compute_driver_score(self, driver_id: uuid.UUID) -> Optional[DriverScoreType]:
        """Compute and save score on demand, return result."""
        from scoring.services import compute_and_save
        from django.utils import timezone
        result = compute_and_save(str(driver_id))
        return DriverScoreType(
            driver_id=driver_id,
            score=result["score"],
            km_driven=result["km_driven"],
            calculated_at=timezone.now(),
        )
