import pytest
from rest_framework import status
from tenants.models import Organization, Tenant, Domain
from tenants.tests.conftest import get_access_token


@pytest.mark.django_db
def test_admin_tenant_create(client, tenant_setup):
    """
    Except for superusers, Tenant admin is the only user that can create a new tenant.
    """
    admin_user = tenant_setup["users"]["admins"][0]
    tenant1 = tenant_setup["tenants"][0]
    domain_url = tenant_setup["domains"][tenant1].domain_url

    client.defaults['HTTP_HOST'] = domain_url

    access_token = get_access_token(client, domain_url, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "New Tenant", "domain_url": "new_tenant.example.com"}
    response = client.post("/api/tenants/", data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == data.get("name")

    tenant_id = response.json()["id"]

    created_tenant = Tenant.objects.get(id=tenant_id)

    assert created_tenant
    assert created_tenant.domain


@pytest.mark.django_db
def test_other_users_tenant_create(client, tenant_setup):
    """
    No other user roles can create tenants.
    """
    user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    domain_url = tenant_setup["domains"][tenant1].domain_url

    client.defaults['HTTP_HOST'] = domain_url

    access_token = get_access_token(client, domain_url, user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "New Tenant", "domain_url": "new_tenant.example.com"}
    response = client.post("/api/tenants/", data, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN

    user = tenant_setup["users"]["organizations"][0]

    access_token = get_access_token(client, domain_url, user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "New Tenant", "domain_url": "new_tenant.example.com"}
    response = client.post("/api/tenants/", data, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN

    user = tenant_setup["users"]["departments"][0]

    access_token = get_access_token(client, domain_url, user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "New Tenant", "domain_url": "new_tenant.example.com"}
    response = client.post("/api/tenants/", data, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN

    user = tenant_setup["users"]["customers"][0]

    access_token = get_access_token(client, domain_url, user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "New Tenant", "domain_url": "new_tenant.example.com"}
    response = client.post("/api/tenants/", data, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN

