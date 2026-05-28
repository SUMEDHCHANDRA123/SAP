"""
Anomaly detection engine for emissions records.
Detects outliers, duplicates, and suspicious patterns.
"""
from decimal import Decimal
from django.db.models import Q
import statistics
from core.models import EmissionRecord, Tenant
from .models import AnomalyFlag


class AnomalyDetector:
    """Detect anomalies and suspicious patterns in emission records."""

    OUTLIER_Z_SCORE_THRESHOLD = 2.5  # 2.5 standard deviations
    UNUSUAL_CHANGE_THRESHOLD = 0.20  # 20% change

    def __init__(self, tenant: Tenant):
        self.tenant = tenant

    def detect_outliers_by_source_scope(self, source_type: str, scope: str):
        """Detect statistical outliers for a specific source-scope combo."""
        records = EmissionRecord.objects.filter(
            tenant=self.tenant,
            source_type=source_type,
            scope=scope,
            status=EmissionRecord.Status.APPROVED,
        ).exclude(normalized_value__isnull=True)

        if records.count() < 3:
            return  # Need at least 3 records for statistical analysis

        values = [float(r.normalized_value) for r in records]

        try:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)
        except (ValueError, statistics.StatisticsError):
            return

        if stdev == 0:
            return  # All values identical, no outliers

        # Find outliers
        outliers = []
        for record in records:
            value = float(record.normalized_value)
            z_score = (value - mean) / stdev if stdev > 0 else 0

            if abs(z_score) > self.OUTLIER_Z_SCORE_THRESHOLD:
                outliers.append((record, z_score, value))

        # Create anomaly flags for outliers
        for record, z_score, value in outliers:
            description = f"Statistical outlier (Z-score: {z_score:.2f}). Expected range: {mean - 2*stdev:.2f} - {mean + 2*stdev:.2f}, Actual: {value:.2f}"

            AnomalyFlag.objects.get_or_create(
                record=record,
                anomaly_type=AnomalyFlag.AnomalyType.OUTLIER,
                defaults={
                    "tenant": self.tenant,
                    "severity": "high" if abs(z_score) > 3 else "medium",
                    "description": description,
                    "metadata": {
                        "z_score": round(z_score, 2),
                        "mean": round(mean, 2),
                        "stdev": round(stdev, 2),
                        "value": round(value, 2),
                    },
                },
            )

    def detect_zero_values(self):
        """Flag zero or null normalized values."""
        records = EmissionRecord.objects.filter(
            tenant=self.tenant,
            status=EmissionRecord.Status.APPROVED,
        ).filter(Q(normalized_value__isnull=True) | Q(normalized_value=0))

        for record in records:
            AnomalyFlag.objects.get_or_create(
                record=record,
                anomaly_type=AnomalyFlag.AnomalyType.ZERO_VALUE,
                defaults={
                    "tenant": self.tenant,
                    "severity": "low",
                    "description": "Record has zero or null normalized value. This may indicate missing data or calculation error.",
                    "metadata": {
                        "activity_value": str(record.activity_value),
                        "normalized_value": str(record.normalized_value),
                    },
                },
            )

    def detect_unit_mismatches(self):
        """Flag records with unexpected activity units."""
        records = EmissionRecord.objects.filter(
            tenant=self.tenant, status=EmissionRecord.Status.APPROVED
        )

        # Define expected units by source type
        expected_units = {
            "SAP_FUEL": ["liters", "gallons", "m3", "kg"],
            "UTILITY_ELECTRICITY": ["kWh", "MWh", "units"],
            "TRAVEL_FLIGHT": ["km", "miles"],
            "TRAVEL_HOTEL": ["nights", "room-nights"],
            "TRAVEL_GROUND": ["km", "miles"],
        }

        for record in records:
            expected = expected_units.get(record.source_type, [])
            unit_lower = record.activity_unit.lower()

            # Check if unit is unexpected
            if expected and not any(
                exp.lower() in unit_lower or unit_lower in exp.lower()
                for exp in expected
            ):
                AnomalyFlag.objects.get_or_create(
                    record=record,
                    anomaly_type=AnomalyFlag.AnomalyType.UNIT_MISMATCH,
                    defaults={
                        "tenant": self.tenant,
                        "severity": "medium",
                        "description": f"Unexpected unit '{record.activity_unit}' for {record.source_type}. Expected one of: {', '.join(expected)}",
                        "metadata": {
                            "activity_unit": record.activity_unit,
                            "source_type": record.source_type,
                            "expected_units": expected,
                        },
                    },
                )

    def detect_duplicate_entries(self, source_type: str = None):
        """Detect potential duplicate entries."""
        records_qs = EmissionRecord.objects.filter(
            tenant=self.tenant, status=EmissionRecord.Status.APPROVED
        )

        if source_type:
            records_qs = records_qs.filter(source_type=source_type)

        # Group by raw data to find duplicates
        raw_data_groups = {}
        for record in records_qs:
            key = str(record.raw_data)
            if key not in raw_data_groups:
                raw_data_groups[key] = []
            raw_data_groups[key].append(record)

        # Flag duplicates
        for raw_data_key, record_list in raw_data_groups.items():
            if len(record_list) > 1:
                for i, record in enumerate(record_list[1:], start=2):
                    AnomalyFlag.objects.get_or_create(
                        record=record,
                        anomaly_type=AnomalyFlag.AnomalyType.DUPLICATE,
                        defaults={
                            "tenant": self.tenant,
                            "severity": "high",
                            "description": f"Potential duplicate entry. Similar raw data found in record #{record_list[0].id}",
                            "metadata": {
                                "duplicate_of_record_id": record_list[0].id,
                                "duplicate_count": len(record_list),
                            },
                        },
                    )

    def detect_unusual_changes(self):
        """Detect unusual increases/decreases compared to historical average."""
        records = EmissionRecord.objects.filter(
            tenant=self.tenant, status=EmissionRecord.Status.APPROVED
        ).order_by("source_type", "scope", "created_at")

        # Group by source and scope
        groups = {}
        for record in records:
            key = (record.source_type, record.scope)
            if key not in groups:
                groups[key] = []
            groups[key].append(record)

        # Analyze each group
        for key, group_records in groups.items():
            if len(group_records) < 3:
                continue

            values = [
                float(r.normalized_value)
                for r in group_records
                if r.normalized_value is not None
            ]
            if len(values) < 3:
                continue

            avg = sum(values) / len(values)

            # Check recent records for unusual changes
            for record in group_records[-10:]:
                if record.normalized_value is None:
                    continue

                value = float(record.normalized_value)
                change = (value - avg) / avg if avg > 0 else 0

                if change > self.UNUSUAL_CHANGE_THRESHOLD:
                    description = f"Unusual increase of {change*100:.1f}% compared to historical average of {avg:.2f}"
                    AnomalyFlag.objects.get_or_create(
                        record=record,
                        anomaly_type=AnomalyFlag.AnomalyType.UNUSUAL_INCREASE,
                        defaults={
                            "tenant": self.tenant,
                            "severity": "medium",
                            "description": description,
                            "metadata": {
                                "percent_change": round(change * 100, 2),
                                "historical_avg": round(avg, 2),
                                "current_value": round(value, 2),
                            },
                        },
                    )
                elif change < -self.UNUSUAL_CHANGE_THRESHOLD:
                    description = f"Unusual decrease of {abs(change)*100:.1f}% compared to historical average of {avg:.2f}"
                    AnomalyFlag.objects.get_or_create(
                        record=record,
                        anomaly_type=AnomalyFlag.AnomalyType.UNUSUAL_DECREASE,
                        defaults={
                            "tenant": self.tenant,
                            "severity": "low",
                            "description": description,
                            "metadata": {
                                "percent_change": round(change * 100, 2),
                                "historical_avg": round(avg, 2),
                                "current_value": round(value, 2),
                            },
                        },
                    )

    def run_full_scan(self):
        """Run all anomaly detection checks."""
        # Check each source-scope combination for outliers
        for source_type in EmissionRecord.SourceType:
            for scope in EmissionRecord.Scope:
                self.detect_outliers_by_source_scope(source_type[0], scope[0])

        # Run other checks
        self.detect_zero_values()
        self.detect_unit_mismatches()
        self.detect_duplicate_entries()
        self.detect_unusual_changes()

    def acknowledge_anomaly(
        self, anomaly_id: int, acknowledged_by: str = None
    ) -> AnomalyFlag:
        """Mark an anomaly as acknowledged by reviewer."""
        anomaly = AnomalyFlag.objects.get(id=anomaly_id)
        anomaly.is_acknowledged = True
        anomaly.acknowledged_by = acknowledged_by or "system"
        anomaly.acknowledged_at = __import__("django.utils.timezone", fromlist=["now"]).now()
        anomaly.save()
        return anomaly

    def get_unacknowledged_anomalies(self, limit: int = 50) -> list:
        """Get unacknowledged anomalies for review."""
        return AnomalyFlag.objects.filter(
            tenant=self.tenant, is_acknowledged=False
        ).order_by("-severity", "-created_at")[:limit]
