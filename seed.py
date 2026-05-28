import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "breathe_esg_backend.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from core.models import Tenant, TenantMembership, EmissionFactor, DataQualityRule, UserProfile  # noqa: E402


def run():
    User = get_user_model()

    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(username="admin", password="admin123")
        print("Created superuser admin/admin123")
    else:
        print("Superuser 'admin' already exists")
    admin_user = User.objects.get(username="admin")
    profile, _ = UserProfile.objects.get_or_create(
        user=admin_user,
        defaults={"approval_status": UserProfile.ApprovalStatus.APPROVED},
    )
    if profile.approval_status != UserProfile.ApprovalStatus.APPROVED:
        profile.approval_status = UserProfile.ApprovalStatus.APPROVED
        profile.save(update_fields=["approval_status"])

    tenant, created = Tenant.objects.get_or_create(
        name="Demo Corp", defaults={"slug": "demo-corp"}
    )
    if created:
        print("Created tenant:", tenant.name, tenant.slug)
    else:
        print("Found tenant:", tenant.name, tenant.slug)

    TenantMembership.objects.get_or_create(
        tenant=tenant,
        user=admin_user,
        defaults={"role": TenantMembership.Role.ADMIN},
    )

    EmissionFactor.objects.get_or_create(
        tenant=tenant,
        source_type="UTILITY_ELECTRICITY",
        scope="SCOPE_2",
        input_unit="kwh",
        year=2024,
        version="demo-v1",
        defaults={
            "value": "0.82",
            "source_name": "Demo Grid Factor",
            "region": "IN",
        },
    )
    EmissionFactor.objects.get_or_create(
        tenant=tenant,
        source_type="SAP_FUEL",
        scope="SCOPE_1",
        input_unit="liters",
        year=2024,
        version="demo-v1",
        defaults={
            "value": "2.68",
            "source_name": "Demo Fuel Factor",
            "region": "IN",
        },
    )

    DataQualityRule.objects.get_or_create(
        tenant=tenant,
        code="MISSING_REQUIRED_FIELD",
        defaults={
            "description": "Required field is missing in source row.",
            "severity": DataQualityRule.Severity.HIGH,
            "rule_config": {"type": "required_field"},
            "is_active": True,
        },
    )


if __name__ == "__main__":
    run()

