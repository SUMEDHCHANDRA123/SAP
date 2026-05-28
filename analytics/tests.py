from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Tenant


class AnalyticsEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        Tenant.objects.create(name="Analytics Corp")

    def test_summary_endpoint(self):
        response = self.client.get("/api/analytics/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("grand_total", response.json())

    def test_refresh_endpoint(self):
        response = self.client.post("/api/analytics/refresh/")
        self.assertEqual(response.status_code, 200)
