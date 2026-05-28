import hashlib
import csv

from django.conf import settings
from django.db import models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout, get_user_model
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework import status as http_status
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    UserProfile,
    Tenant,
    TenantMembership,
    IngestionJob,
    EmissionRecord,
    IngestionTemplate,
    EmissionFactor,
    DataQualitySnapshot,
    AuditEvent,
    ReductionTarget,
    SimulationScenario,
    BenchmarkSnapshot,
    ApprovalDecision,
)
from .permissions import IsTenantReviewerOrAbove, has_tenant_membership
from .serializers import (
    TenantSerializer,
    EmissionRecordSerializer,
    EmissionRecordListSerializer,
    IngestionJobSerializer,
    IngestionTemplateSerializer,
    EmissionFactorSerializer,
    DataQualitySnapshotSerializer,
    AuditEventSerializer,
    ReductionTargetSerializer,
    SimulationScenarioSerializer,
    BenchmarkSnapshotSerializer,
    PendingUserSerializer,
)
from .services.ingestion_service import process_ingestion_job
from .services.workflow_service import apply_decision, log_audit
from .tasks import process_ingestion_job_task


def _get_tenant(request):
    """Resolve tenant for current request, defaulting to first tenant."""
    tenant_id = request.query_params.get("tenant_id")
    if tenant_id:
        tenant = get_object_or_404(Tenant, pk=tenant_id)
        if getattr(settings, "ENFORCE_TENANT_MEMBERSHIP", False):
            if not has_tenant_membership(request.user, tenant):
                raise ValidationError("You do not have access to this tenant.")
        return tenant
    if getattr(settings, "REQUIRE_TENANT_ID", False):
        raise ValidationError("tenant_id is required")
    tenant = Tenant.objects.order_by("id").first()
    if not tenant:
        raise ValidationError("No Tenant exists. Run seed.py or create one in admin.")
    if getattr(settings, "ENFORCE_TENANT_MEMBERSHIP", False):
        if not has_tenant_membership(request.user, tenant):
            raise ValidationError("You do not have access to this tenant.")
    return tenant


def _ensure_user_profile(user):
    status = (
        UserProfile.ApprovalStatus.APPROVED
        if user.is_superuser
        else UserProfile.ApprovalStatus.PENDING
    )
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={"approval_status": status},
    )
    if user.is_superuser and profile.approval_status != UserProfile.ApprovalStatus.APPROVED:
        profile.approval_status = UserProfile.ApprovalStatus.APPROVED
        profile.save(update_fields=["approval_status"])
    return profile


def _user_is_approved(user) -> bool:
    if user.is_superuser:
        return True
    profile = _ensure_user_profile(user)
    return profile.approval_status == UserProfile.ApprovalStatus.APPROVED


def _require_platform_admin(request):
    if not request.user or not request.user.is_authenticated:
        raise ValidationError("Authentication required")
    if request.user.is_superuser:
        return
    is_admin = TenantMembership.objects.filter(
        user=request.user,
        role=TenantMembership.Role.ADMIN,
    ).exists()
    if not is_admin:
        raise ValidationError("Admin permissions required")


class AuthMeView(APIView):
    authentication_classes = [SessionAuthentication]

    @method_decorator(csrf_exempt)
    def post(self, request):
        username = (request.data or {}).get("username", "").strip()
        password = (request.data or {}).get("password", "")
        if not username or not password:
            return Response(
                {"detail": "username and password are required"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response(
                {"detail": "Invalid credentials"},
                status=http_status.HTTP_401_UNAUTHORIZED,
            )
        if not _user_is_approved(user):
            return Response(
                {
                    "detail": "Account pending admin approval. You can sign in after an admin approves your account.",
                    "approval_status": _ensure_user_profile(user).approval_status,
                },
                status=http_status.HTTP_403_FORBIDDEN,
            )
        login(request, user)
        return self.get(request)

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return Response(
                {"authenticated": False, "user": None, "memberships": []},
                status=http_status.HTTP_200_OK,
            )
        memberships = [
            {
                "tenant_id": m.tenant_id,
                "tenant_name": m.tenant.name,
                "tenant_slug": m.tenant.slug,
                "role": m.role,
            }
            for m in user.tenant_memberships.select_related("tenant").all().order_by("tenant__name")
        ]
        profile = _ensure_user_profile(user)
        return Response(
            {
                "authenticated": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "is_superuser": user.is_superuser,
                    "approval_status": profile.approval_status,
                },
                "memberships": memberships,
            }
        )

    @method_decorator(csrf_exempt)
    def delete(self, request):
        logout(request)
        if hasattr(request, "session"):
            request.session.flush()
        return Response({"authenticated": False}, status=http_status.HTTP_200_OK)


class AuthRegisterView(APIView):
    authentication_classes = []

    @method_decorator(csrf_exempt)
    def post(self, request):
        username = (request.data or {}).get("username", "").strip()
        password = (request.data or {}).get("password", "")
        if not username or not password:
            return Response(
                {"detail": "username and password are required"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            return Response(
                {"detail": "Username already exists"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.create_user(username=username, password=password)
        _ensure_user_profile(user)
        return Response(
            {
                "detail": "Registration successful. Wait for admin approval before signing in.",
                "username": user.username,
                "approval_status": UserProfile.ApprovalStatus.PENDING,
            },
            status=http_status.HTTP_201_CREATED,
        )


class AdminPendingUsersView(APIView):
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        try:
            _require_platform_admin(request)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_403_FORBIDDEN)

        User = get_user_model()
        users = User.objects.filter(is_superuser=False).select_related("profile").order_by("-date_joined")
        payload = []
        for user in users:
            profile = _ensure_user_profile(user)
            if profile.approval_status != UserProfile.ApprovalStatus.PENDING:
                continue
            payload.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "approval_status": profile.approval_status,
                    "created_at": profile.created_at,
                    "has_membership": user.tenant_memberships.exists(),
                }
            )
        return Response(PendingUserSerializer(payload, many=True).data)


class AdminApproveUserView(APIView):
    authentication_classes = [SessionAuthentication]

    def patch(self, request, user_id: int):
        try:
            _require_platform_admin(request)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_403_FORBIDDEN)

        User = get_user_model()
        user = get_object_or_404(User, pk=user_id)
        if user.is_superuser:
            return Response({"detail": "Cannot modify superuser"}, status=http_status.HTTP_400_BAD_REQUEST)

        profile = _ensure_user_profile(user)
        profile.approval_status = UserProfile.ApprovalStatus.APPROVED
        profile.approved_by = request.user
        profile.approved_at = timezone.now()
        profile.save(update_fields=["approval_status", "approved_by", "approved_at"])

        tenant_id = (request.data or {}).get("tenant_id")
        role = (request.data or {}).get("role", TenantMembership.Role.ANALYST)
        if tenant_id:
            tenant = get_object_or_404(Tenant, pk=tenant_id)
            TenantMembership.objects.update_or_create(
                tenant=tenant,
                user=user,
                defaults={"role": role},
            )

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "approval_status": profile.approval_status,
                "detail": "User approved",
            }
        )


class IngestBaseView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    source_type = None

    def post(self, request):
        if "file" not in request.FILES:
            return Response(
                {"detail": "Missing multipart field 'file'."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant = _get_tenant(request)
        except Exception as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

        upload = request.FILES["file"]
        upload_bytes = upload.read()
        upload.seek(0)
        idempotency_hash = hashlib.sha256(upload_bytes).hexdigest()

        existing = IngestionJob.objects.filter(
            tenant=tenant,
            source_type=self.source_type,
            idempotency_hash=idempotency_hash,
            status__in=[IngestionJob.Status.QUEUED, IngestionJob.Status.PROCESSING, IngestionJob.Status.DONE],
        ).first()
        if existing:
            return Response(
                {
                    "job_id": existing.id,
                    "status": existing.status,
                    "row_count": existing.row_count,
                    "error_count": existing.error_count,
                    "errors": existing.error_log,
                    "detail": "Duplicate ingestion detected; reusing existing job.",
                },
                status=http_status.HTTP_200_OK,
            )

        user = (
            request.user
            if getattr(request, "user", None) is not None and request.user.is_authenticated
            else None
        )

        job = IngestionJob.objects.create(
            tenant=tenant,
            source_type=self.source_type,
            file_name=upload.name,
            uploaded_file=upload,
            uploaded_by=user,
            status=IngestionJob.Status.QUEUED,
            idempotency_key=request.headers.get("Idempotency-Key", ""),
            idempotency_hash=idempotency_hash,
        )
        log_audit("ingestion_queued", job=job, actor=user, payload={"file_name": upload.name})

        if settings.CELERY_TASK_ALWAYS_EAGER:
            process_ingestion_job(job.id)
        else:
            process_ingestion_job_task.delay(job.id)

        return Response(
            {
                "job_id": job.id,
                "status": job.status,
                "row_count": job.row_count,
                "error_count": job.error_count,
                "errors": job.error_log,
            },
            status=http_status.HTTP_200_OK,
        )


class TenantListView(APIView):
    def get(self, request):
        qs = Tenant.objects.order_by("name")
        if (
            getattr(settings, "ENFORCE_TENANT_MEMBERSHIP", False)
            and getattr(request, "user", None)
            and request.user.is_authenticated
            and not request.user.is_superuser
        ):
            qs = qs.filter(memberships__user=request.user).distinct()
        return Response(TenantSerializer(qs, many=True).data)


class IngestSapView(IngestBaseView):
    source_type = IngestionJob.SourceType.SAP_FUEL


class IngestSapProcurementView(IngestBaseView):
    source_type = IngestionJob.SourceType.SAP_PROCUREMENT


class IngestUtilityView(IngestBaseView):
    source_type = IngestionJob.SourceType.UTILITY_ELECTRICITY


class IngestTravelView(IngestBaseView):
    source_type = IngestionJob.SourceType.TRAVEL


class EmissionRecordListView(APIView):
    def get(self, request):
        tenant = _get_tenant(request)
        qs = EmissionRecord.objects.filter(tenant=tenant).annotate(
            anomaly_count=models.Count("anomalies", filter=models.Q(anomalies__is_acknowledged=False))
        )

        status_q = request.query_params.get("status")
        source_type_q = request.query_params.get("source_type")
        job_q = request.query_params.get("job")
        scope_q = request.query_params.get("scope")
        has_anomalies_q = request.query_params.get("has_anomalies")

        if status_q:
            qs = qs.filter(status=status_q)
        if source_type_q:
            qs = qs.filter(source_type=source_type_q)
        if job_q:
            qs = qs.filter(job_id=job_q)
        if scope_q:
            qs = qs.filter(scope=scope_q)
        if has_anomalies_q in {"1", "true", "yes"}:
            qs = qs.filter(anomaly_count__gt=0)

        data = EmissionRecordListSerializer(qs, many=True).data
        return Response(data)


class EmissionRecordDetailView(APIView):
    def get(self, request, pk: int):
        tenant = _get_tenant(request)
        rec = get_object_or_404(EmissionRecord, pk=pk, tenant=tenant)
        return Response(EmissionRecordSerializer(rec).data)


class ApproveRecordView(APIView):
    permission_classes = [IsTenantReviewerOrAbove]

    def patch(self, request, pk: int):
        tenant = _get_tenant(request)
        rec = get_object_or_404(EmissionRecord, pk=pk, tenant=tenant)
        self.check_object_permissions(request, rec)
        if rec.is_locked:
            return Response(
                {"detail": "Record is locked."},
                status=http_status.HTTP_409_CONFLICT,
            )
        rec = apply_decision(rec, ApprovalDecision.Decision.APPROVED, actor=request.user)
        return Response(EmissionRecordSerializer(rec).data)


class RejectRecordView(APIView):
    permission_classes = [IsTenantReviewerOrAbove]

    def patch(self, request, pk: int):
        tenant = _get_tenant(request)
        rec = get_object_or_404(EmissionRecord, pk=pk, tenant=tenant)
        self.check_object_permissions(request, rec)
        if rec.is_locked:
            return Response(
                {"detail": "Record is locked."},
                status=http_status.HTTP_409_CONFLICT,
            )

        note = (request.data or {}).get("note", "")
        rec = apply_decision(rec, ApprovalDecision.Decision.REJECTED, note=note, actor=request.user)
        return Response(EmissionRecordSerializer(rec).data)


class FlagRecordView(APIView):
    permission_classes = [IsTenantReviewerOrAbove]

    def patch(self, request, pk: int):
        tenant = _get_tenant(request)
        rec = get_object_or_404(EmissionRecord, pk=pk, tenant=tenant)
        self.check_object_permissions(request, rec)
        if rec.is_locked:
            return Response(
                {"detail": "Record is locked."},
                status=http_status.HTTP_409_CONFLICT,
            )

        reason = (request.data or {}).get("reason", "")
        rec = apply_decision(rec, ApprovalDecision.Decision.FLAGGED, note=reason, actor=request.user)
        return Response(EmissionRecordSerializer(rec).data)


class JobListView(APIView):
    def get(self, request):
        tenant = _get_tenant(request)
        qs = IngestionJob.objects.filter(tenant=tenant)
        return Response(IngestionJobSerializer(qs, many=True).data)


class JobErrorExportView(APIView):
    def get(self, request, pk: int):
        tenant = _get_tenant(request)
        job = get_object_or_404(IngestionJob, pk=pk, tenant=tenant)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="job_{job.id}_errors.csv"'
        writer = csv.writer(response)
        writer.writerow(["row_number", "reason"])
        for err in job.error_log or []:
            writer.writerow([err.get("row_number"), err.get("reason", "")])
        return response


class IngestionTemplateListCreateView(APIView):
    def get(self, request):
        tenant = _get_tenant(request)
        qs = IngestionTemplate.objects.filter(tenant=tenant)
        return Response(IngestionTemplateSerializer(qs, many=True).data)

    def post(self, request):
        tenant = _get_tenant(request)
        serializer = IngestionTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            tenant=tenant,
            created_by=request.user if getattr(request.user, "is_authenticated", False) else None,
        )
        return Response(serializer.data, status=http_status.HTTP_201_CREATED)


class EmissionFactorListCreateView(APIView):
    def get(self, request):
        tenant = _get_tenant(request)
        qs = EmissionFactor.objects.filter(models.Q(tenant=tenant) | models.Q(tenant__isnull=True))
        return Response(EmissionFactorSerializer(qs, many=True).data)

    def post(self, request):
        tenant = _get_tenant(request)
        serializer = EmissionFactorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(tenant=tenant)
        return Response(serializer.data, status=http_status.HTTP_201_CREATED)


class DataQualitySnapshotListView(APIView):
    def get(self, request):
        tenant = _get_tenant(request)
        qs = DataQualitySnapshot.objects.filter(tenant=tenant).order_by("-created_at")
        return Response(DataQualitySnapshotSerializer(qs, many=True).data)


class AuditEventListView(APIView):
    def get(self, request):
        tenant = _get_tenant(request)
        qs = AuditEvent.objects.filter(tenant=tenant).order_by("-created_at")[:500]
        return Response(AuditEventSerializer(qs, many=True).data)


class ReductionTargetListCreateView(APIView):
    def get(self, request):
        tenant = _get_tenant(request)
        qs = ReductionTarget.objects.filter(tenant=tenant).order_by("-updated_at")
        return Response(ReductionTargetSerializer(qs, many=True).data)

    def post(self, request):
        tenant = _get_tenant(request)
        serializer = ReductionTargetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            tenant=tenant,
            owner=request.user if getattr(request.user, "is_authenticated", False) else None,
        )
        return Response(serializer.data, status=http_status.HTTP_201_CREATED)


class SimulationScenarioListCreateView(APIView):
    def get(self, request):
        tenant = _get_tenant(request)
        qs = SimulationScenario.objects.filter(tenant=tenant).order_by("-updated_at")
        return Response(SimulationScenarioSerializer(qs, many=True).data)

    def post(self, request):
        tenant = _get_tenant(request)
        serializer = SimulationScenarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assumptions = serializer.validated_data.get("assumptions", {})
        pct_reduction = assumptions.get("percent_reduction", 0)
        current_total = EmissionRecord.objects.filter(tenant=tenant, co2e_kg__isnull=False).aggregate(
            total=models.Sum("co2e_kg")
        )["total"] or 0
        projected_delta = current_total * (pct_reduction / 100)
        projected_total = current_total - projected_delta

        serializer.save(
            tenant=tenant,
            created_by=request.user if getattr(request.user, "is_authenticated", False) else None,
            projected_delta_kg=projected_delta,
            projected_total_kg=projected_total,
        )
        return Response(serializer.data, status=http_status.HTTP_201_CREATED)


class BenchmarkSnapshotListView(APIView):
    def get(self, request):
        tenant = _get_tenant(request)
        qs = BenchmarkSnapshot.objects.filter(tenant=tenant).order_by("-date")
        return Response(BenchmarkSnapshotSerializer(qs, many=True).data)

