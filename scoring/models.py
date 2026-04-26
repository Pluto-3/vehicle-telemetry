from django.db import models
from drivers.models import Driver

class DriverScore(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="scores")
    score = models.FloatField()
    km_driven = models.FloatField(default=0.0)
    window_Days = models.IntegerField(default=30)
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-calculated_at"]
        indexes = [
            models.Index(fields=["driver", "calculated_at"]),
        ]

    def __str__(self):
        return f"{self.driver_id} score={self.score:.1f} @ {self.calculated_at}"