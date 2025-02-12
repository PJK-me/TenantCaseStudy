from rest_framework.exceptions import NotFound

from tenants.middleware import get_current_tenant


class TenantMixin:

    def get_tenant(self):
        tenant = get_current_tenant()
        if not tenant:
            raise NotFound("Tenant not found or not authorized.")
        return tenant