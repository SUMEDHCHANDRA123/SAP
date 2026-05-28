from rest_framework import serializers
from .models import EmissionsSummary, AnomalyFlag, TrendAnalysis


class EmissionsSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionsSummary
        fields = [
            "id",
            "tenant",
            "period",
            "date",
            "scope_1_total",
            "scope_2_total",
            "scope_3_total",
            "grand_total",
            "source_breakdown",
            "record_count",
            "last_updated",
        ]


class AnomalyFlagSerializer(serializers.ModelSerializer):
    record_id = serializers.SerializerMethodField()
    source_type = serializers.SerializerMethodField()
    scope = serializers.SerializerMethodField()

    class Meta:
        model = AnomalyFlag
        fields = [
            "id",
            "record_id",
            "source_type",
            "scope",
            "anomaly_type",
            "severity",
            "description",
            "metadata",
            "is_acknowledged",
            "created_at",
        ]

    def get_record_id(self, obj):
        return obj.record.id

    def get_source_type(self, obj):
        return obj.record.source_type

    def get_scope(self, obj):
        return obj.record.scope


class TrendAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrendAnalysis
        fields = [
            "id",
            "tenant",
            "source_type",
            "scope",
            "period_start",
            "period_end",
            "total_emissions",
            "record_count",
            "avg_emissions",
            "min_emissions",
            "max_emissions",
            "percent_change",
        ]
