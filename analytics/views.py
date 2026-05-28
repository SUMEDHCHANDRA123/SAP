from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.http import HttpResponse
from datetime import datetime, timedelta
import csv

from core.models import Tenant, EmissionRecord, ReductionTarget, BenchmarkSnapshot, SimulationScenario
from .models import EmissionsSummary, AnomalyFlag
from .calculators import EmissionsCalculator
from .anomaly_detector import AnomalyDetector
from .serializers import (
    EmissionsSummarySerializer,
    AnomalyFlagSerializer,
)


def _get_tenant(request):
    """Resolve tenant for current request, defaulting to first tenant."""
    tenant_id = request.query_params.get("tenant_id")
    if tenant_id:
        return get_object_or_404(Tenant, pk=tenant_id)
    from django.conf import settings
    if getattr(settings, "REQUIRE_TENANT_ID", False):
        raise ValueError("tenant_id is required")
    tenant = Tenant.objects.order_by("id").first()
    if not tenant:
        raise ValueError("No Tenant exists. Run seed.py or create one in admin.")
    return tenant


class AnalyticsSummaryView(APIView):
    """Get overall emissions summary (total by scope)."""

    def get(self, request):
        try:
            tenant = _get_tenant(request)
        except Exception as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

        # Get or calculate total summary
        summary = EmissionsSummary.objects.filter(
            tenant=tenant, period="total"
        ).first()

        if not summary:
            calculator = EmissionsCalculator(tenant)
            summary = calculator.calculate_total_summary()

        serializer = EmissionsSummarySerializer(summary)
        return Response(serializer.data)


class AnalyticsBreakdownView(APIView):
    """Get emissions breakdown by scope or source type."""

    def get(self, request):
        try:
            tenant = _get_tenant(request)
        except Exception as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

        group_by = request.query_params.get("group_by", "scope")  # scope or source

        calculator = EmissionsCalculator(tenant)

        if group_by == "source":
            breakdown = calculator.calculate_breakdown_by_source()
        else:
            breakdown = calculator.calculate_breakdown_by_scope()

        return Response({"breakdown": breakdown, "group_by": group_by})


class AnalyticsTrendsView(APIView):
    """Get emissions trends over time."""

    def get(self, request):
        try:
            tenant = _get_tenant(request)
        except Exception as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

        period = request.query_params.get("period", "monthly")  # daily or monthly
        months_back = int(request.query_params.get("months_back", 12))
        source_type = request.query_params.get("source_type")
        scope = request.query_params.get("scope")

        calculator = EmissionsCalculator(tenant)
        trends = calculator.calculate_monthly_trends(
            source_type=source_type, scope=scope, months_back=months_back
        )

        return Response({"trends": trends, "period": period})


class AnomaliesListView(APIView):
    """Get detected anomalies for review."""

    def get(self, request):
        try:
            tenant = _get_tenant(request)
        except Exception as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

        # Get filter parameters
        severity = request.query_params.get("severity")
        anomaly_type = request.query_params.get("type")
        acknowledged_only = request.query_params.get("acknowledged") == "true"
        limit = int(request.query_params.get("limit", 50))

        anomalies_qs = AnomalyFlag.objects.filter(tenant=tenant)

        if severity:
            anomalies_qs = anomalies_qs.filter(severity=severity)
        if anomaly_type:
            anomalies_qs = anomalies_qs.filter(anomaly_type=anomaly_type)
        if acknowledged_only:
            anomalies_qs = anomalies_qs.filter(is_acknowledged=True)
        else:
            anomalies_qs = anomalies_qs.filter(is_acknowledged=False)

        anomalies = anomalies_qs.order_by("-severity", "-created_at")[:limit]

        serializer = AnomalyFlagSerializer(anomalies, many=True)
        return Response(serializer.data)


class AnomaliesDetailView(APIView):
    """Get details of a specific anomaly."""

    def get(self, request, pk: int):
        anomaly = get_object_or_404(AnomalyFlag, pk=pk)
        serializer = AnomalyFlagSerializer(anomaly)
        return Response(serializer.data)

    def patch(self, request, pk: int):
        """Acknowledge an anomaly."""
        anomaly = get_object_or_404(AnomalyFlag, pk=pk)

        detector = AnomalyDetector(anomaly.tenant)
        user_name = (
            request.user.username
            if getattr(request, "user", None) and request.user.is_authenticated
            else "system"
        )
        detector.acknowledge_anomaly(pk, acknowledged_by=user_name)

        anomaly.refresh_from_db()
        serializer = AnomalyFlagSerializer(anomaly)
        return Response(serializer.data)


class RefreshAnalyticsView(APIView):
    """Manually trigger analytics refresh."""

    def post(self, request):
        try:
            tenant = _get_tenant(request)
        except Exception as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

        # Refresh all summaries
        calculator = EmissionsCalculator(tenant)
        calculator.refresh_all_summaries()

        # Run anomaly detection
        detector = AnomalyDetector(tenant)
        detector.run_full_scan()

        return Response(
            {"detail": "Analytics refreshed successfully"},
            status=http_status.HTTP_200_OK,
        )


class TargetProgressView(APIView):
    """Get progress against configured reduction targets."""

    def get(self, request):
        try:
            tenant = _get_tenant(request)
        except Exception as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

        targets = ReductionTarget.objects.filter(tenant=tenant).order_by("-updated_at")
        current_total = EmissionRecord.objects.filter(
            tenant=tenant, status=EmissionRecord.Status.APPROVED
        ).aggregate(total=Sum("co2e_kg"))["total"] or 0

        out = []
        for t in targets:
            baseline = float(t.baseline_value)
            target = float(t.target_value)
            current = float(current_total)
            achieved = ((baseline - current) / (baseline - target) * 100) if baseline != target else 0
            out.append(
                {
                    "id": t.id,
                    "name": t.name,
                    "scope": t.scope,
                    "baseline_year": t.baseline_year,
                    "target_year": t.target_year,
                    "baseline_value": baseline,
                    "target_value": target,
                    "current_value": current,
                    "progress_percent": round(max(min(achieved, 100), 0), 2),
                }
            )
        return Response(out)


class BenchmarkOverviewView(APIView):
    """Get benchmark metrics by period."""

    def get(self, request):
        try:
            tenant = _get_tenant(request)
        except Exception as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

        metric = request.query_params.get("metric")
        qs = BenchmarkSnapshot.objects.filter(tenant=tenant)
        if metric:
            qs = qs.filter(metric=metric)
        data = [
            {
                "id": row.id,
                "metric": row.metric,
                "period": row.period,
                "date": row.date.isoformat(),
                "value": float(row.value),
                "denominator": float(row.denominator) if row.denominator is not None else None,
                "metadata": row.metadata,
            }
            for row in qs.order_by("-date")[:200]
        ]
        return Response(data)


class ScenarioOverviewView(APIView):
    """Get saved simulation scenarios."""

    def get(self, request):
        try:
            tenant = _get_tenant(request)
        except Exception as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

        scenarios = SimulationScenario.objects.filter(tenant=tenant).order_by("-updated_at")
        return Response(
            [
                {
                    "id": s.id,
                    "name": s.name,
                    "assumptions": s.assumptions,
                    "projected_delta_kg": float(s.projected_delta_kg),
                    "projected_total_kg": float(s.projected_total_kg),
                    "updated_at": s.updated_at.isoformat(),
                }
                for s in scenarios
            ]
        )


class ReportExportView(APIView):
    """Export approved records report as CSV."""

    def get(self, request):
        try:
            tenant = _get_tenant(request)
        except Exception as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

        records = EmissionRecord.objects.filter(tenant=tenant, status=EmissionRecord.Status.APPROVED).order_by("-created_at")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="breathe_esg_report_{tenant.slug}.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "record_id",
                "source_type",
                "scope",
                "activity_value",
                "activity_unit",
                "co2e_kg",
                "factor_value",
                "factor_version",
                "created_at",
            ]
        )
        for r in records:
            writer.writerow(
                [
                    r.id,
                    r.source_type,
                    r.scope,
                    r.activity_value,
                    r.activity_unit,
                    r.co2e_kg,
                    r.factor_value,
                    r.factor_version,
                    r.created_at.isoformat(),
                ]
            )
        return response
