from io import BytesIO

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient

from core.models import EmissionFactor, IngestionJob, Tenant, UserProfile
from core.parsers.sap_procurement_parser import parse_sap_procurement_csv
from core.parsers.sap_parser import parse_sap_fuel_csv
from core.parsers.travel_parser import parse_travel_concur_csv
from core.parsers.utility_parser import parse_utility_electricity_csv


class IngestionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="Test Corp")

    def test_missing_file_returns_400(self):
        response = self.client.post("/api/ingest/sap/")
        self.assertEqual(response.status_code, 400)

    def test_jobs_endpoint_returns_list(self):
        response = self.client.get("/api/jobs/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)


class FactorModelTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Factor Corp")

    def test_create_factor(self):
        factor = EmissionFactor.objects.create(
            tenant=self.tenant,
            source_type="UTILITY_ELECTRICITY",
            scope="SCOPE_2",
            input_unit="kwh",
            year=2024,
            value="0.82",
            version="v1",
        )
        self.assertAlmostEqual(float(factor.value), 0.82, places=8)


class MembershipTests(TestCase):
    def test_tenant_membership_role_flow(self):
        tenant = Tenant.objects.create(name="Member Corp")
        user = get_user_model().objects.create_user(username="reviewer", password="pass123")
        from core.models import TenantMembership

        membership = TenantMembership.objects.create(
            tenant=tenant,
            user=user,
            role=TenantMembership.Role.REVIEWER,
        )
        self.assertEqual(membership.role, TenantMembership.Role.REVIEWER)


class QualitySnapshotTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Quality Corp")
        self.user = get_user_model().objects.create_user(username="ingestor")
        self.job = IngestionJob.objects.create(
            tenant=self.tenant,
            source_type=IngestionJob.SourceType.SAP_FUEL,
            file_name="demo.csv",
            uploaded_by=self.user,
        )

    def test_quality_fields_default(self):
        self.assertEqual(self.job.quality_score, 0)
        self.assertEqual(self.job.quality_summary, {})


class ParserEnhancementTests(TestCase):
    def test_sap_fuel_parser_accepts_alias_headers_and_resolves_plant(self):
        csv_data = (
            "Quantity,Unit,PostingDate,Plant\n"
            "45,L,2024-03-11,PL01\n"
        )
        result = parse_sap_fuel_csv(BytesIO(csv_data.encode("utf-8")))
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["raw_data"]["plant_name"], "Mumbai Plant")

    def test_utility_prorates_billing_period_across_months(self):
        csv_data = (
            "meter_id,site_name,billing_period_start,billing_period_end,consumption_kwh,supplier\n"
            "M1,HQ,2024-01-20,2024-02-10,220,GridCo\n"
        )
        result = parse_utility_electricity_csv(BytesIO(csv_data.encode("utf-8")))
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["records"]), 2)
        jan = result["records"][0]
        feb = result["records"][1]
        self.assertEqual(jan["raw_data"]["allocation_start"], "2024-01-20")
        self.assertEqual(jan["raw_data"]["allocation_end"], "2024-01-31")
        self.assertEqual(feb["raw_data"]["allocation_start"], "2024-02-01")
        self.assertEqual(feb["raw_data"]["allocation_end"], "2024-02-10")

    def test_utility_rejects_non_kwh_unit(self):
        csv_data = (
            "meter_id,site_name,billing_period_start,billing_period_end,consumption_kwh,unit,supplier\n"
            "M1,HQ,2024-01-20,2024-02-10,220,mwh,GridCo\n"
        )
        result = parse_utility_electricity_csv(BytesIO(csv_data.encode("utf-8")))
        self.assertEqual(len(result["records"]), 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Unsupported electricity unit", result["errors"][0]["reason"])

    def test_travel_infers_distance_from_iata(self):
        csv_data = (
            "trip_id,category,travel_date,origin,destination,distance_km,nights,cost_usd,department\n"
            "T1,Flight,2024-01-02,BOM,DEL,,0,0,Ops\n"
        )
        result = parse_travel_concur_csv(BytesIO(csv_data.encode("utf-8")))
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["records"]), 1)
        self.assertGreater(float(result["records"][0]["activity_value"]), 1000.0)

    def test_sap_procurement_parser_creates_scope3_records(self):
        csv_data = (
            "EBELN,EBELP,WERKS,MATNR,MENGE,MEINS,NETWR,WAERS,BLDAT,LIFNR,BKTXT\n"
            "4500001,10,PL01,MAT1,120,KG,0,INR,15.01.2024,V001,Test row\n"
        )
        result = parse_sap_procurement_csv(BytesIO(csv_data.encode("utf-8")))
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["scope"], "SCOPE_3")
        self.assertEqual(result["records"][0]["source_type"], "SAP_PROCUREMENT")


class StrictTenantTests(TestCase):
    @override_settings(REQUIRE_TENANT_ID=True)
    def test_jobs_endpoint_requires_tenant_when_enabled(self):
        client = APIClient()
        Tenant.objects.create(name="Tenant A")
        response = client.get("/api/jobs/")
        self.assertEqual(response.status_code, 400)


class AuthAndExportTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="Ops Corp")
        self.user = get_user_model().objects.create_user(username="analyst", password="pass123")
        UserProfile.objects.filter(user=self.user).update(
            approval_status=UserProfile.ApprovalStatus.APPROVED
        )
        self.job = IngestionJob.objects.create(
            tenant=self.tenant,
            source_type=IngestionJob.SourceType.SAP_FUEL,
            file_name="bad.csv",
            error_log=[{"row_number": 2, "reason": "Bad unit"}],
            error_count=1,
        )

    def test_auth_me_for_anonymous(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["authenticated"], False)

    def test_auth_me_login_success(self):
        response = self.client.post(
            "/api/auth/me/",
            {"username": "analyst", "password": "pass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["authenticated"], True)
        self.assertEqual(response.json()["user"]["username"], "analyst")

    def test_pending_user_cannot_login(self):
        User = get_user_model()
        pending = User.objects.create_user(username="pending_user", password="pass123")
        UserProfile.objects.update_or_create(
            user=pending,
            defaults={"approval_status": UserProfile.ApprovalStatus.PENDING},
        )
        response = self.client.post(
            "/api/auth/me/",
            {"username": "pending_user", "password": "pass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_register_creates_pending_user(self):
        response = self.client.post(
            "/api/auth/register/",
            {"username": "new_user", "password": "pass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        profile = UserProfile.objects.get(user__username="new_user")
        self.assertEqual(profile.approval_status, UserProfile.ApprovalStatus.PENDING)

    def test_job_error_export_downloads_csv(self):
        response = self.client.get(f"/api/jobs/{self.job.id}/errors.csv")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        self.assertIn("row_number,reason", body)
        self.assertIn("2,Bad unit", body)
