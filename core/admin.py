from django.contrib import admin

from .models import (
    UserProfile,
    Tenant,
    IngestionJob,
    EmissionRecord,
    TenantMembership,
    IngestionTemplate,
    DataQualityRule,
    DataQualitySnapshot,
    EmissionFactor,
    ApprovalWorkflow,
    ApprovalDecision,
    AuditEvent,
    ReductionTarget,
    SimulationScenario,
    BenchmarkSnapshot,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "approval_status", "approved_by", "approved_at", "created_at")
    list_filter = ("approval_status",)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "created_at")
    search_fields = ("name", "slug")


@admin.register(IngestionJob)
class IngestionJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "source_type",
        "file_name",
        "status",
        "row_count",
        "error_count",
        "uploaded_at",
    )
    list_filter = ("source_type", "status", "uploaded_at")
    search_fields = ("file_name", "tenant__name", "tenant__slug")
    readonly_fields = ("uploaded_at",)


@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "job",
        "source_type",
        "scope",
        "status",
        "is_locked",
        "created_at",
    )
    list_filter = ("source_type", "scope", "status", "is_locked")
    search_fields = ("tenant__name", "tenant__slug", "job__file_name")
    readonly_fields = ("created_at", "updated_at")


admin.site.register(TenantMembership)
admin.site.register(IngestionTemplate)
admin.site.register(DataQualityRule)
admin.site.register(DataQualitySnapshot)
admin.site.register(EmissionFactor)
admin.site.register(ApprovalWorkflow)
admin.site.register(ApprovalDecision)
admin.site.register(AuditEvent)
admin.site.register(ReductionTarget)
admin.site.register(SimulationScenario)
admin.site.register(BenchmarkSnapshot)

