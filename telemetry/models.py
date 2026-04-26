from django.db import models
from vehicles.models import Vehicle


class Telemetry(models.Model):
    # High insert volume, no UUID needed here
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="telemetry")
    # source_id: client-generated idempotency key  e.g. "{vehicle_id}:{timestamp_ms}:{seq}"
    source_id = models.CharField(max_length=128)
    timestamp = models.DateTimeField(db_index=True)
    speed = models.FloatField()          # km/h
    fuel_level = models.FloatField()     # 0–100 %
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["vehicle", "timestamp"]),  # critical — all range queries use this
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["vehicle", "source_id"],
                name="unique_telemetry_source"
            )
        ]

    def __str__(self):
        return f"{self.vehicle_id} @ {self.timestamp} — {self.speed} km/h"