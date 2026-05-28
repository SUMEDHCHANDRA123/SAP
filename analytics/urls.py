from django.urls import path
from .views import (
    AnalyticsSummaryView,
    AnalyticsBreakdownView,
    AnalyticsTrendsView,
    AnomaliesListView,
    AnomaliesDetailView,
    RefreshAnalyticsView,
    TargetProgressView,
    BenchmarkOverviewView,
    ScenarioOverviewView,
    ReportExportView,
)

urlpatterns = [
    path("summary/", AnalyticsSummaryView.as_view(), name="analytics-summary"),
    path("breakdown/", AnalyticsBreakdownView.as_view(), name="analytics-breakdown"),
    path("trends/", AnalyticsTrendsView.as_view(), name="analytics-trends"),
    path("anomalies/", AnomaliesListView.as_view(), name="anomalies-list"),
    path("anomalies/<int:pk>/", AnomaliesDetailView.as_view(), name="anomalies-detail"),
    path("refresh/", RefreshAnalyticsView.as_view(), name="analytics-refresh"),
    path("targets/", TargetProgressView.as_view(), name="analytics-targets"),
    path("benchmarks/", BenchmarkOverviewView.as_view(), name="analytics-benchmarks"),
    path("scenarios/", ScenarioOverviewView.as_view(), name="analytics-scenarios"),
    path("reports/export.csv", ReportExportView.as_view(), name="analytics-report-export"),
]
