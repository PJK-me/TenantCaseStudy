from functools import wraps
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Tenant, Domain


def tenant_scope(func):
    @wraps(func)

    def wrapper(request, *args, **kwargs):
        domain_url = request.get_host()

        try:
            domain = get_object_or_404(Domain, name=domain_url)
            try:
                tenant = get_object_or_404(Tenant, domain=domain)
            except Tenant.DoesNotExist:
                return JsonResponse({'error': 'tenant associated with this domain does not exist'}, status=404)

        except Domain.DoesNotExist:
            return JsonResponse({'error': 'Domain does not exist'}, status=404)

        request.tenant = tenant
        
        return func(request, *args, **kwargs)
    return wrapper

