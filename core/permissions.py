from rest_framework.permissions import BasePermission

from core.models import TenantMembership


def has_tenant_membership(user, tenant) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return TenantMembership.objects.filter(tenant=tenant, user=user).exists()


class IsTenantReviewerOrAbove(BasePermission):
    message = "You do not have reviewer permissions for this tenant."

    def has_object_permission(self, request, view, obj):
        if has_tenant_membership(request.user, obj.tenant) is False:
            return False
        if request.user.is_superuser:
            return True
        membership = TenantMembership.objects.filter(
            tenant=obj.tenant,
            user=request.user,
        ).first()
        if not membership:
            return False
        return membership.role in {
            TenantMembership.Role.REVIEWER,
            TenantMembership.Role.MANAGER,
            TenantMembership.Role.ADMIN,
        }
