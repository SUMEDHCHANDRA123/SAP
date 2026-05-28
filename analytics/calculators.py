"""
Calculation engine for aggregating emissions data.
Handles totals by scope, source type, and time-based aggregations.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Min, Max, Q
from django.db import transaction
from core.models import EmissionRecord, Tenant
from .models import EmissionsSummary, TrendAnalysis


class EmissionsCalculator:
    """Calculate and cache emissions summaries."""

    def __init__(self, tenant: Tenant):
        self.tenant = tenant

    def calculate_total_summary(self) -> EmissionsSummary:
        """Calculate total emissions across all records."""
        records = EmissionRecord.objects.filter(
            tenant=self.tenant, status=EmissionRecord.Status.APPROVED
        )

        # Calculate by scope
        scope_1_records = records.filter(scope=EmissionRecord.Scope.SCOPE_1)
        scope_2_records = records.filter(scope=EmissionRecord.Scope.SCOPE_2)
        scope_3_records = records.filter(scope=EmissionRecord.Scope.SCOPE_3)

        scope_1_total = (
            scope_1_records.aggregate(Sum("normalized_value"))["normalized_value__sum"]
            or Decimal("0")
        )
        scope_2_total = (
            scope_2_records.aggregate(Sum("normalized_value"))["normalized_value__sum"]
            or Decimal("0")
        )
        scope_3_total = (
            scope_3_records.aggregate(Sum("normalized_value"))["normalized_value__sum"]
            or Decimal("0")
        )

        grand_total = scope_1_total + scope_2_total + scope_3_total

        # Source breakdown
        source_breakdown = {}
        for source_type in EmissionRecord.SourceType:
            source_records = records.filter(source_type=source_type[0])
            total = (
                source_records.aggregate(Sum("normalized_value"))[
                    "normalized_value__sum"
                ]
                or Decimal("0")
            )
            if total > 0:
                source_breakdown[source_type[0]] = float(total)

        # Get or create summary
        summary, _ = EmissionsSummary.objects.get_or_create(
            tenant=self.tenant,
            period="total",
            date=None,
            defaults={
                "scope_1_total": scope_1_total,
                "scope_2_total": scope_2_total,
                "scope_3_total": scope_3_total,
                "grand_total": grand_total,
                "source_breakdown": source_breakdown,
                "record_count": records.count(),
            },
        )

        # Update if already exists
        summary.scope_1_total = scope_1_total
        summary.scope_2_total = scope_2_total
        summary.scope_3_total = scope_3_total
        summary.grand_total = grand_total
        summary.source_breakdown = source_breakdown
        summary.record_count = records.count()
        summary.save()

        return summary

    def calculate_daily_summary(self, date: datetime.date = None) -> EmissionsSummary:
        """Calculate emissions for a specific day."""
        if date is None:
            date = datetime.now().date()

        records = EmissionRecord.objects.filter(
            tenant=self.tenant,
            status=EmissionRecord.Status.APPROVED,
            created_at__date=date,
        )

        scope_1_total = (
            records.filter(scope=EmissionRecord.Scope.SCOPE_1).aggregate(
                Sum("normalized_value")
            )["normalized_value__sum"]
            or Decimal("0")
        )
        scope_2_total = (
            records.filter(scope=EmissionRecord.Scope.SCOPE_2).aggregate(
                Sum("normalized_value")
            )["normalized_value__sum"]
            or Decimal("0")
        )
        scope_3_total = (
            records.filter(scope=EmissionRecord.Scope.SCOPE_3).aggregate(
                Sum("normalized_value")
            )["normalized_value__sum"]
            or Decimal("0")
        )

        grand_total = scope_1_total + scope_2_total + scope_3_total

        # Source breakdown
        source_breakdown = {}
        for source_type in EmissionRecord.SourceType:
            source_records = records.filter(source_type=source_type[0])
            total = (
                source_records.aggregate(Sum("normalized_value"))[
                    "normalized_value__sum"
                ]
                or Decimal("0")
            )
            if total > 0:
                source_breakdown[source_type[0]] = float(total)

        summary, _ = EmissionsSummary.objects.get_or_create(
            tenant=self.tenant,
            period="daily",
            date=date,
            defaults={
                "scope_1_total": scope_1_total,
                "scope_2_total": scope_2_total,
                "scope_3_total": scope_3_total,
                "grand_total": grand_total,
                "source_breakdown": source_breakdown,
                "record_count": records.count(),
            },
        )

        summary.scope_1_total = scope_1_total
        summary.scope_2_total = scope_2_total
        summary.scope_3_total = scope_3_total
        summary.grand_total = grand_total
        summary.source_breakdown = source_breakdown
        summary.record_count = records.count()
        summary.save()

        return summary

    def calculate_monthly_summary(self, year: int = None, month: int = None):
        """Calculate emissions for a specific month."""
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month

        records = EmissionRecord.objects.filter(
            tenant=self.tenant,
            status=EmissionRecord.Status.APPROVED,
            created_at__year=year,
            created_at__month=month,
        )

        date = datetime(year, month, 1).date()

        scope_1_total = (
            records.filter(scope=EmissionRecord.Scope.SCOPE_1).aggregate(
                Sum("normalized_value")
            )["normalized_value__sum"]
            or Decimal("0")
        )
        scope_2_total = (
            records.filter(scope=EmissionRecord.Scope.SCOPE_2).aggregate(
                Sum("normalized_value")
            )["normalized_value__sum"]
            or Decimal("0")
        )
        scope_3_total = (
            records.filter(scope=EmissionRecord.Scope.SCOPE_3).aggregate(
                Sum("normalized_value")
            )["normalized_value__sum"]
            or Decimal("0")
        )

        grand_total = scope_1_total + scope_2_total + scope_3_total

        source_breakdown = {}
        for source_type in EmissionRecord.SourceType:
            source_records = records.filter(source_type=source_type[0])
            total = (
                source_records.aggregate(Sum("normalized_value"))[
                    "normalized_value__sum"
                ]
                or Decimal("0")
            )
            if total > 0:
                source_breakdown[source_type[0]] = float(total)

        summary, _ = EmissionsSummary.objects.get_or_create(
            tenant=self.tenant,
            period="monthly",
            date=date,
            defaults={
                "scope_1_total": scope_1_total,
                "scope_2_total": scope_2_total,
                "scope_3_total": scope_3_total,
                "grand_total": grand_total,
                "source_breakdown": source_breakdown,
                "record_count": records.count(),
            },
        )

        summary.scope_1_total = scope_1_total
        summary.scope_2_total = scope_2_total
        summary.scope_3_total = scope_3_total
        summary.grand_total = grand_total
        summary.source_breakdown = source_breakdown
        summary.record_count = records.count()
        summary.save()

        return summary

    def calculate_breakdown_by_source(self) -> dict:
        """Get breakdown of total emissions by source type."""
        records = EmissionRecord.objects.filter(
            tenant=self.tenant, status=EmissionRecord.Status.APPROVED
        )

        breakdown = {}
        for code, label in EmissionRecord.SourceType.choices:
            total = (
                records.filter(source_type=code).aggregate(
                    Sum("normalized_value")
                )["normalized_value__sum"]
                or Decimal("0")
            )
            breakdown[label] = {  # Use human-readable name
                "value": float(total),
                "code": code,
            }

        return breakdown

    def calculate_breakdown_by_scope(self) -> dict:
        """Get breakdown of total emissions by scope."""
        records = EmissionRecord.objects.filter(
            tenant=self.tenant, status=EmissionRecord.Status.APPROVED
        )

        breakdown = {}
        for code, label in EmissionRecord.Scope.choices:
            total = (
                records.filter(scope=code).aggregate(Sum("normalized_value"))[
                    "normalized_value__sum"
                ]
                or Decimal("0")
            )
            breakdown[label] = {  # Use human-readable name
                "value": float(total),
                "code": code,
            }

        return breakdown

    def calculate_monthly_trends(
        self, source_type: str = None, scope: str = None, months_back: int = 12
    ) -> list:
        """Calculate monthly trend data for the last N months."""
        records_qs = EmissionRecord.objects.filter(
            tenant=self.tenant, status=EmissionRecord.Status.APPROVED
        )

        if source_type:
            records_qs = records_qs.filter(source_type=source_type)
        if scope:
            records_qs = records_qs.filter(scope=scope)

        now = datetime.now()
        trends = []

        for i in range(months_back, 0, -1):
            target_date = now - timedelta(days=30 * i)
            year = target_date.year
            month = target_date.month

            month_records = records_qs.filter(
                created_at__year=year, created_at__month=month
            )

            total = (
                month_records.aggregate(Sum("normalized_value"))[
                    "normalized_value__sum"
                ]
                or Decimal("0")
            )
            avg = (
                month_records.aggregate(Sum("normalized_value"))[
                    "normalized_value__sum"
                ]
                or Decimal("0")
            ) / max(month_records.count(), 1)

            trends.append(
                {
                    "date": f"{year}-{month:02d}",
                    "total": float(total),
                    "average": float(avg),
                    "count": month_records.count(),
                }
            )

        return trends

    def refresh_all_summaries(self):
        """Refresh all cached summary data for tenant."""
        with transaction.atomic():
            # Clear old summaries
            EmissionsSummary.objects.filter(tenant=self.tenant).delete()

            # Recalculate
            self.calculate_total_summary()

            # Calculate last 30 days
            for i in range(30):
                date = datetime.now().date() - timedelta(days=i)
                self.calculate_daily_summary(date)

            # Calculate last 12 months
            for i in range(12):
                target_date = datetime.now() - timedelta(days=30 * i)
                self.calculate_monthly_summary(target_date.year, target_date.month)
