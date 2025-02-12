import os
import pytest
import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
django.setup()

@pytest.fixture(scope='session', autouse=True)
def setup_django():
    django.setup()

from tenants.models import Tenant, Domain

@pytest.fixture
def tenant_setup(db):
    tenant1 = Tenant.objects.create(name="Tenant1")
    tenant2 = Tenant.objects.create(name="Tenant2")

    domain1 = Domain.objects.create(tenant=tenant1, domain_url="tenant1.example.com")
    domain2 = Domain.objects.create(tenant=tenant2, domain_url="tenant2.example.com")

    return tenant1, tenant2, domain1, domain2