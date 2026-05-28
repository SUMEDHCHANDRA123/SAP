from django.core.management.base import BaseCommand
from core.models import Tenant
from analytics.calculators import EmissionsCalculator
from analytics.anomaly_detector import AnomalyDetector


class Command(BaseCommand):
    help = "Refresh all analytics data (summaries and anomalies)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant-id",
            type=int,
            help="Specific tenant ID to refresh. If not provided, refreshes all tenants.",
        )

    def handle(self, *args, **options):
        tenant_id = options.get("tenant_id")

        if tenant_id:
            tenants = Tenant.objects.filter(id=tenant_id)
        else:
            tenants = Tenant.objects.all()

        if not tenants.exists():
            self.stdout.write(self.style.ERROR("No tenants found"))
            return

        for tenant in tenants:
            self.stdout.write(f"\nProcessing tenant: {tenant.name}")

            # Refresh summaries
            self.stdout.write("  - Refreshing emissions summaries...")
            calculator = EmissionsCalculator(tenant)
            calculator.refresh_all_summaries()

            # Detect anomalies
            self.stdout.write("  - Running anomaly detection...")
            detector = AnomalyDetector(tenant)
            detector.run_full_scan()

            self.stdout.write(self.style.SUCCESS(f"  ✓ {tenant.name} analytics updated"))

        self.stdout.write(self.style.SUCCESS("\n✓ All analytics refreshed successfully"))
