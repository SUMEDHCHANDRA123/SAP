from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Tenant(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "tenant"
            slug = base
            i = 2
            while Tenant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class IngestionJob(models.Model):
    class SourceType(models.TextChoices):
        SAP_FUEL = "SAP_FUEL", "SAP Fuel"
        SAP_PROCUREMENT = "SAP_PROCUREMENT", "SAP Procurement"
        UTILITY_ELECTRICITY = "UTILITY_ELECTRICITY", "Utility Electricity"
        TRAVEL = "TRAVEL", "Travel"

    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        PROCESSING = "PROCESSING", "Processing"
        DONE = "DONE", "Done"
        FAILED = "FAILED", "Failed"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="jobs")
    source_type = models.CharField(max_length=32, choices=SourceType.choices)
    file_name = models.CharField(max_length=255)
    uploaded_file = models.FileField(
        upload_to="ingestion_uploads/",
        null=True,
        blank=True,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ingestion_jobs",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PROCESSING
    )
    row_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    error_log = models.JSONField(default=list, blank=True)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    quality_summary = models.JSONField(default=dict, blank=True)
    idempotency_key = models.CharField(max_length=128, blank=True)
    idempotency_hash = models.CharField(max_length=128, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return f"{self.tenant.slug} {self.source_type} {self.uploaded_at:%Y-%m-%d %H:%M}"


class EmissionRecord(models.Model):
    class SourceType(models.TextChoices):
        SAP_FUEL = "SAP_FUEL", "SAP Fuel"
        SAP_PROCUREMENT = "SAP_PROCUREMENT", "SAP Procurement"
        UTILITY_ELECTRICITY = "UTILITY_ELECTRICITY", "Utility Electricity"
        TRAVEL_FLIGHT = "TRAVEL_FLIGHT", "Travel Flight"
        TRAVEL_HOTEL = "TRAVEL_HOTEL", "Travel Hotel"
        TRAVEL_GROUND = "TRAVEL_GROUND", "Travel Ground"

    class Scope(models.TextChoices):
        SCOPE_1 = "SCOPE_1", "Scope 1"
        SCOPE_2 = "SCOPE_2", "Scope 2"
        SCOPE_3 = "SCOPE_3", "Scope 3"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        FLAGGED = "FLAGGED", "Flagged"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="records"
    )
    job = models.ForeignKey(
        IngestionJob, on_delete=models.CASCADE, related_name="records"
    )

    source_type = models.CharField(max_length=32, choices=SourceType.choices)
    scope = models.CharField(max_length=16, choices=Scope.choices)

    activity_value = models.DecimalField(max_digits=12, decimal_places=4)
    activity_unit = models.CharField(max_length=64)
    normalized_value = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )

    raw_data = models.JSONField()

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    is_locked = models.BooleanField(default=False)
    approval_stage = models.CharField(max_length=32, default="ANALYST_REVIEW")

    flag_reason = models.TextField(blank=True)
    reject_note = models.TextField(blank=True)
    quality_flags = models.JSONField(default=list, blank=True)

    co2e_kg = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    factor_value = models.DecimalField(max_digits=16, decimal_places=8, null=True, blank=True)
    factor_unit = models.CharField(max_length=64, blank=True)
    factor_version = models.CharField(max_length=64, blank=True)
    factor_source = models.CharField(max_length=128, blank=True)
    factor_region = models.CharField(max_length=64, blank=True)
    factor_year = models.IntegerField(null=True, blank=True)
    calc_trace = models.JSONField(default=dict, blank=True)

    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="edited_emission_records",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.tenant.slug} {self.source_type} {self.scope} {self.status}"


class UserProfile(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    approval_status = models.CharField(
        max_length=16,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_users",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user_id} {self.approval_status}"


class TenantMembership(models.Model):
    class Role(models.TextChoices):
        ANALYST = "ANALYST", "Analyst"
        REVIEWER = "REVIEWER", "Reviewer"
        MANAGER = "MANAGER", "Manager"
        ADMIN = "ADMIN", "Admin"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_memberships",
    )
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.ANALYST)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "user")

    def __str__(self) -> str:
        return f"{self.user_id} {self.tenant.slug} {self.role}"


class IngestionTemplate(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="ingestion_templates")
    source_type = models.CharField(max_length=32, choices=IngestionJob.SourceType.choices)
    name = models.CharField(max_length=120)
    vendor_name = models.CharField(max_length=120, blank=True)
    column_mapping = models.JSONField(default=dict, blank=True)
    required_columns = models.JSONField(default=list, blank=True)
    validation_rules = models.JSONField(default=dict, blank=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_templates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = ("tenant", "source_type", "name")

    def __str__(self) -> str:
        return f"{self.tenant.slug} {self.source_type} {self.name}"


class DataQualityRule(models.Model):
    class Severity(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="quality_rules")
    source_type = models.CharField(max_length=32, blank=True)
    code = models.CharField(max_length=64)
    description = models.TextField()
    rule_config = models.JSONField(default=dict, blank=True)
    severity = models.CharField(max_length=8, choices=Severity.choices, default=Severity.MEDIUM)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "code")

    def __str__(self) -> str:
        return f"{self.tenant.slug} {self.code}"


class DataQualitySnapshot(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="quality_snapshots")
    job = models.OneToOneField(IngestionJob, on_delete=models.CASCADE, related_name="quality_snapshot")
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_rows = models.IntegerField(default=0)
    valid_rows = models.IntegerField(default=0)
    flagged_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    issue_breakdown = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.tenant.slug} job-{self.job_id} score-{self.score}"


class EmissionFactor(models.Model):
    class FactorKind(models.TextChoices):
        ACTIVITY_TO_CO2E = "ACTIVITY_TO_CO2E", "Activity to CO2e"

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="emission_factors",
        null=True,
        blank=True,
    )
    source_type = models.CharField(max_length=32, blank=True)
    scope = models.CharField(max_length=16, choices=EmissionRecord.Scope.choices, blank=True)
    factor_kind = models.CharField(max_length=32, choices=FactorKind.choices, default=FactorKind.ACTIVITY_TO_CO2E)
    input_unit = models.CharField(max_length=64)
    output_unit = models.CharField(max_length=32, default="kg_co2e")
    region = models.CharField(max_length=64, blank=True)
    year = models.IntegerField()
    value = models.DecimalField(max_digits=16, decimal_places=8)
    version = models.CharField(max_length=64)
    source_name = models.CharField(max_length=128, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-updated_at"]

    def __str__(self) -> str:
        return f"{self.input_unit}->{self.output_unit} {self.value} ({self.year})"


class ApprovalWorkflow(models.Model):
    class Stage(models.TextChoices):
        ANALYST_REVIEW = "ANALYST_REVIEW", "Analyst Review"
        REVIEWER_REVIEW = "REVIEWER_REVIEW", "Reviewer Review"
        MANAGER_SIGNOFF = "MANAGER_SIGNOFF", "Manager Signoff"
        COMPLETED = "COMPLETED", "Completed"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="approval_workflows")
    record = models.OneToOneField(EmissionRecord, on_delete=models.CASCADE, related_name="approval_workflow")
    current_stage = models.CharField(max_length=32, choices=Stage.choices, default=Stage.ANALYST_REVIEW)
    is_completed = models.BooleanField(default=False)
    due_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"workflow-{self.record_id} {self.current_stage}"


class ApprovalDecision(models.Model):
    class Decision(models.TextChoices):
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        FLAGGED = "FLAGGED", "Flagged"

    workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.CASCADE, related_name="decisions")
    stage = models.CharField(max_length=32, choices=ApprovalWorkflow.Stage.choices)
    decision = models.CharField(max_length=16, choices=Decision.choices)
    note = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approval_decisions",
    )
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["decided_at"]


class AuditEvent(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="audit_events")
    event_type = models.CharField(max_length=64)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    job = models.ForeignKey(
        IngestionJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    record = models.ForeignKey(
        EmissionRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ReductionTarget(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="reduction_targets")
    name = models.CharField(max_length=120)
    scope = models.CharField(max_length=16, choices=EmissionRecord.Scope.choices, blank=True)
    baseline_year = models.IntegerField()
    baseline_value = models.DecimalField(max_digits=16, decimal_places=4)
    target_year = models.IntegerField()
    target_value = models.DecimalField(max_digits=16, decimal_places=4)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_targets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SimulationScenario(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="simulation_scenarios")
    name = models.CharField(max_length=120)
    assumptions = models.JSONField(default=dict, blank=True)
    projected_delta_kg = models.DecimalField(max_digits=16, decimal_places=4, default=0)
    projected_total_kg = models.DecimalField(max_digits=16, decimal_places=4, default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_scenarios",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class BenchmarkSnapshot(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="benchmark_snapshots")
    metric = models.CharField(max_length=64)  # kg_per_employee, kg_per_revenue, etc.
    period = models.CharField(max_length=16, default="monthly")
    date = models.DateField()
    value = models.DecimalField(max_digits=16, decimal_places=6)
    denominator = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

