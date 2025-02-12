from functools import wraps
from django.http import HttpResponseForbidden
from .middleware import get_current_tenant

def tenant_scope_required(cls):
    original_dispatch = cls.dispatch

    @wraps(original_dispatch)
    def new_dispatch(self, request, *args, **kwargs):
        tenant = get_current_tenant()

        if not tenant:
            return HttpResponseForbidden("Tenant not found or not authorized.")

        kwargs["tenant"] = tenant
        return original_dispatch(self, request, *args, **kwargs)

    cls.dispatch = new_dispatch
    return cls