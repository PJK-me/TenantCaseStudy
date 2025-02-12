import pytest
from rest_framework.test import APIClient
from tenants.models import Organization


@pytest.mark.django_db
def test_create_organization_with_tenant_separation(tenant_setup):
    tenant1, tenant2, domain1, domain2 = tenant_setup
    client = APIClient()

    client.defaults['HTTP_HOST'] = domain1.domain_url

    response = client.post(
        "/api/create/organization/",
        {"name": "Org A"},
        format="json"
    )

    assert response.status_code == 201
    assert Organization.objects.filter(tenant=tenant1).exists()
    assert not Organization.objects.filter(tenant=tenant2).exists()
    assert response.data["name"] == "Org A"
    assert response.data["tenant"] == tenant1.id