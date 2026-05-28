from django.contrib import admin
from .models import EmissionsSummary, AnomalyFlag, TrendAnalysis


@admin.register(EmissionsSummary)
class EmissionsSummaryAdmin(admin.ModelAdmin):
    list_display = [
        "tenant",
        "period",
        "date",
        "grand_total",
        "record_count",
        "last_updated",
    ]
    list_filter = ["tenant", "period", "date"]
    search_fields = ["tenant__name"]
    readonly_fields = ["last_updated"]


@admin.register(AnomalyFlag)
class AnomalyFlagAdmin(admin.ModelAdmin):
    list_display = [
        "record",
        "anomaly_type",
        "severity",
        "is_acknowledged",
        "created_at",
    ]
    list_filter = ["anomaly_type", "severity", "is_acknowledged", "created_at"]
    search_fields = ["record__id", "description"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(TrendAnalysis)
class TrendAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        "tenant",
        "source_type",
        "scope",
        "period_start",
        "period_end",
        "total_emissions",
        "record_count",
    ]
    list_filter = ["tenant", "source_type", "scope", "period_type"]
    search_fields = ["tenant__name"]
    readonly_fields = ["created_at", "updated_at"]
