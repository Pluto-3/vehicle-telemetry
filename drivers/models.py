import uuid
from django.db import models
from vehicles.models import Vehicle


class Driver(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.license_number})"


class VehicleDriverAssignment(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="assignments")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="assignments")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["vehicle_id", "start_time"]),
            models.Index(fields=["driver_id", "start_time"]),
        ]

    def __str__(self):
        return f"{self.driver} -> {self.vehicle}"
