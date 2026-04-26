from django.db import models
from vehicles.models import Vehicle
from drivers.models import Driver

class Eventtype(models.TextChoices):
    HARSH_BRAKE = "HARSH_BRAKE", "Harsh Brake"
    RAPID_ACCEL = "RAPID_ACCEL", "Rapid Acceleration"
    OVERSPEED = "OVERSPEED", "Overspeed"

class DrivingEvent(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="events")
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    event_type = models.CharField(max_length=20, choices=Eventtype.choices)
    severity = models.IntegerField(default=1)
    timestamp = models.DateTimeField(db_index=True)
    speed_before = models.FloatField(null=True)
    speed_after = models.FloatField(null=True)

    class Meta: 
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["vehicle", "timestamp"]),
            models.Index(fields=["driver", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.event_type} | {self.vehicle_id} | sev={self.severity}"