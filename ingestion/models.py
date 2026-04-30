import uuid
import secrets
from django.db import models


class APIKey(models.Model):
    """
    Simple API key for authenticating ingestion clients and simulators.
    Keys are prefixed: "tlm_<32 random hex chars>"
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)          # e.g. "Simulator", "Vehicle Gateway"
    key = models.CharField(max_length=80, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = f"tlm_{secrets.token_hex(32)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({'active' if self.is_active else 'inactive'})"

    class Meta:
        ordering = ["-created_at"]
