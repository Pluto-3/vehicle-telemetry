import strawberry
from datetime import datetime
from typing import Optional
import uuid


@strawberry.type
class VehicleType:
    id: uuid.UUID
    plate_number: str
    model: str
    created_at: datetime


@strawberry.type
class DriverType:
    id: uuid.UUID
    name: str
    license_number: str


@strawberry.type
class TelemetryType:
    id: int
    vehicle_id: uuid.UUID
    timestamp: datetime
    speed: float
    fuel_level: float
    latitude: float
    longitude: float
    source_id: str


@strawberry.type
class DrivingEventType:
    id: int
    vehicle_id: uuid.UUID
    event_type: str
    severity: int
    timestamp: datetime
    speed_before: Optional[float]
    speed_after: Optional[float]


@strawberry.type
class DriverScoreType:
    driver_id: uuid.UUID
    score: float
    km_driven: float
    calculated_at: datetime


@strawberry.type
class IngestResult:
    success: bool
    created: int
    message: str


@strawberry.type
class AssignmentType:
    id: int
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID
    start_time: datetime
    end_time: Optional[datetime]


@strawberry.input
class TelemetryInput:
    vehicle_id: uuid.UUID
    source_id: str
    timestamp: datetime
    speed: float
    fuel_level: float
    latitude: float
    longitude: float


@strawberry.input
class DriverInput:
    name: str
    license_number: str


@strawberry.input
class AssignmentInput:
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID
