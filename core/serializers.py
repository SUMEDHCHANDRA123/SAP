from rest_framework import serializers

from .models import (
    UserProfile,
    Tenant,
    IngestionJob,
    EmissionRecord,
    IngestionTemplate,
    DataQualitySnapshot,
    EmissionFactor,
    AuditEvent,
    ReductionTarget,
    SimulationScenario,
    BenchmarkSnapshot,
)


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "slug"]


class PendingUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    approval_status = serializers.CharField()
    created_at = serializers.DateTimeField()
    has_membership = serializers.BooleanField()


class IngestionJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionJob
        fields = [
            "id",
            "tenant",
            "source_type",
            "file_name",
            "uploaded_by",
            "uploaded_at",
            "status",
            "row_count",
            "error_count",
            "error_log",
            "quality_score",
            "quality_summary",
            "started_at",
            "completed_at",
        ]


class EmissionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionRecord
        fields = [
            "id",
            "tenant",
            "job",
            "source_type",
            "scope",
            "activity_value",
            "activity_unit",
            "normalized_value",
            "raw_data",
            "status",
            "is_locked",
            "approval_stage",
            "flag_reason",
            "reject_note",
            "quality_flags",
            "co2e_kg",
            "factor_value",
            "factor_unit",
            "factor_version",
            "factor_source",
            "factor_region",
            "factor_year",
            "calc_trace",
            "edited_by",
            "created_at",
            "updated_at",
        ]


class EmissionRecordListSerializer(serializers.ModelSerializer):
    anomaly_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = EmissionRecord
        fields = [
            "id",
            "tenant",
            "job",
            "source_type",
            "scope",
            "activity_value",
            "activity_unit",
            "normalized_value",
            "status",
            "is_locked",
            "approval_stage",
            "co2e_kg",
            "anomaly_count",
            "flag_reason",
            "reject_note",
            "created_at",
            "updated_at",
        ]


class IngestionTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionTemplate
        fields = "__all__"


class DataQualitySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataQualitySnapshot
        fields = "__all__"


class EmissionFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionFactor
        fields = "__all__"


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = "__all__"


class ReductionTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReductionTarget
        fields = "__all__"


class SimulationScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationScenario
        fields = "__all__"


class BenchmarkSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkSnapshot
        fields = "__all__"

