from django.db import models
from core.models import Tenant, EmissionRecord


class EmissionsSummary(models.Model):
    """Cache aggregated emissions data for fast dashboard queries."""

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="emissions_summaries"
    )

    # Aggregation keys
    period = models.CharField(
        max_length=32,
        choices=[
            ("total", "Total"),
            ("daily", "Daily"),
            ("monthly", "Monthly"),
            ("yearly", "Yearly"),
        ],
        default="total",
    )
    date = models.DateField(null=True, blank=True)  # For daily/monthly/yearly aggregations

    # Aggregated values
    scope_1_total = models.DecimalField(max_digits=16, decimal_places=4, default=0)
    scope_2_total = models.DecimalField(max_digits=16, decimal_places=4, default=0)
    scope_3_total = models.DecimalField(max_digits=16, decimal_places=4, default=0)
    grand_total = models.DecimalField(max_digits=16, decimal_places=4, default=0)

    # Source breakdown (stored as JSON for flexibility)
    source_breakdown = models.JSONField(default=dict, blank=True)  # {"SAP_FUEL": 1000, ...}
    activity_breakdown = models.JSONField(default=dict, blank=True)  # By activity unit

    # Metadata
    record_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_updated"]
        unique_together = ("tenant", "period", "date")
        verbose_name_plural = "Emissions Summaries"

    def __str__(self) -> str:
        date_str = f" ({self.date})" if self.date else ""
        return f"{self.tenant.slug} {self.period}{date_str}"


class AnomalyFlag(models.Model):
    """Track detected anomalies and suspicious patterns."""

    class AnomalyType(models.TextChoices):
        OUTLIER = "OUTLIER", "Statistical Outlier (Z-Score)"
        DUPLICATE = "DUPLICATE", "Potential Duplicate"
        UNUSUAL_INCREASE = "UNUSUAL_INCREASE", "Unusual Increase (>20%)"
        UNUSUAL_DECREASE = "UNUSUAL_DECREASE", "Unusual Decrease (>20%)"
        ZERO_VALUE = "ZERO_VALUE", "Zero or Null Value"
        UNIT_MISMATCH = "UNIT_MISMATCH", "Unit Inconsistency"

    record = models.ForeignKey(
        EmissionRecord, on_delete=models.CASCADE, related_name="anomalies"
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="anomaly_flags"
    )

    anomaly_type = models.CharField(max_length=32, choices=AnomalyType.choices)
    severity = models.CharField(
        max_length=16,
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
        default="medium",
    )
    description = models.TextField()  # Human-readable explanation
    metadata = models.JSONField(
        default=dict, blank=True
    )  # Store threshold, actual value, expected range, etc.

    is_acknowledged = models.BooleanField(
        default=False
    )  # Has a reviewer acknowledged this anomaly?
    acknowledged_by = models.TextField(blank=True)  # User who acknowledged
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("record", "anomaly_type")

    def __str__(self) -> str:
        return f"{self.record.id} - {self.anomaly_type} ({self.severity})"


class TrendAnalysis(models.Model):
    """Store pre-calculated trend data for performance."""

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="trend_analyses"
    )
    source_type = models.CharField(max_length=32)  # SAP_FUEL, UTILITY_ELECTRICITY, etc.
    scope = models.CharField(max_length=16)  # SCOPE_1, SCOPE_2, SCOPE_3

    period_start = models.DateField()
    period_end = models.DateField()
    period_type = models.CharField(
        max_length=16, choices=[("daily", "Daily"), ("monthly", "Monthly")]
    )

    total_emissions = models.DecimalField(max_digits=16, decimal_places=4)
    record_count = models.IntegerField()
    avg_emissions = models.DecimalField(max_digits=16, decimal_places=4)
    min_emissions = models.DecimalField(max_digits=16, decimal_places=4, null=True)
    max_emissions = models.DecimalField(max_digits=16, decimal_places=4, null=True)

    # Statistics for trend detection
    percent_change = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )  # % change from previous period

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-period_end"]
        unique_together = ("tenant", "source_type", "scope", "period_start", "period_end", "period_type")
        verbose_name_plural = "Trend Analyses"

    def __str__(self) -> str:
        return f"{self.tenant.slug} {self.source_type} {self.period_start}-{self.period_end}"
