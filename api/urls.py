from django.urls import path, include

from core import views


urlpatterns = [
    path("auth/me/", views.AuthMeView.as_view()),
    path("auth/register/", views.AuthRegisterView.as_view()),
    path("admin/users/pending/", views.AdminPendingUsersView.as_view()),
    path("admin/users/<int:user_id>/approve/", views.AdminApproveUserView.as_view()),
    path("tenants/", views.TenantListView.as_view()),
    path("ingest/sap/", views.IngestSapView.as_view()),
    path("ingest/sap-procurement/", views.IngestSapProcurementView.as_view()),
    path("ingest/utility/", views.IngestUtilityView.as_view()),
    path("ingest/travel/", views.IngestTravelView.as_view()),
    path("records/", views.EmissionRecordListView.as_view()),
    path("records/<int:pk>/", views.EmissionRecordDetailView.as_view()),
    path("records/<int:pk>/approve/", views.ApproveRecordView.as_view()),
    path("records/<int:pk>/reject/", views.RejectRecordView.as_view()),
    path("records/<int:pk>/flag/", views.FlagRecordView.as_view()),
    path("jobs/", views.JobListView.as_view()),
    path("jobs/<int:pk>/errors.csv", views.JobErrorExportView.as_view()),
    path("templates/", views.IngestionTemplateListCreateView.as_view()),
    path("factors/", views.EmissionFactorListCreateView.as_view()),
    path("quality-snapshots/", views.DataQualitySnapshotListView.as_view()),
    path("audit-events/", views.AuditEventListView.as_view()),
    path("targets/", views.ReductionTargetListCreateView.as_view()),
    path("scenarios/", views.SimulationScenarioListCreateView.as_view()),
    path("benchmarks/", views.BenchmarkSnapshotListView.as_view()),
    path("analytics/", include("analytics.urls")),
]

