from threading import local
from tenants.models import Tenant
from django.http import Http404
from .tenant_schema import set_tenant_schema

_thread_locals = local()

def get_current_tenant():
    return getattr(_thread_locals, 'tenant', None)

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract tenant based on domain, subdomain, or other logic
        tenant = self.get_tenant_from_request(request)

        # Set the tenant in thread-local storage
        _thread_locals.tenant = tenant

        # Continue processing the request
        response = self.get_response(request)

        return response

    def get_tenant_from_request(self, request):
        # tenant_domain = request.META.get('HTTP_HOST')
        domain = request.get_host()
        try:
            tenant = Tenant.objects.get(domain__domain_url=domain)
            set_tenant_schema(tenant.get_schema_name())
            return tenant
        except Tenant.DoesNotExist:
            return None
