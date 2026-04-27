"""
Management command: compute driver scores for all active drivers.
Run every 6h via cron:  0 */6 * * * python manage.py compute_scores
"""

from django.core.management.base import BaseCommand
from drivers.models import Driver
from scoring.services import compute_and_save

class Command(BaseCommand):
    help = "Compute and snapshot driver scores (30-day rolling window)"

    def handle(self, *args, **kwargs):
        drivers = Driver.objects.all()
        for driver in drivers:
            result = compute_and_save(str(driver.id))
            self.stdout.write(
                f" {driver.name}: score={result['score']} km={result['km_driven']}"
            )
        self.stdout.write(self.style.SUCCESS(f"Scored {drivers.count()} drivers."))