import pytest
from rest_framework import status
from tenants.models import Organization, Tenant, Domain
from tenants.tests.conftest import get_access_token


@pytest.mark.django_db
def test_admin_tenant_retrival(client, tenant_setup):
    """
    Tenant admins and superusers can use GET method, with tenant id to access it
    """
    admin_user = tenant_setup["users"]["admins"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    response = client.get(f"/api/tenants/{tenant1.id}/", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == tenant1.id

    response = client.get(f"/api/tenants/{tenant2.id}/", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == tenant2.id

    client.defaults['HTTP_HOST'] = domain_url2

    response = client.get(f"/api/tenants/{tenant1.id}/", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == tenant1.id

    response = client.get(f"/api/tenants/{tenant2.id}/", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == tenant2.id


@pytest.mark.django_db
def test_tenant_user_tenant_retrival(client, tenant_setup):
    """
    Tenant users can only get tenant they belong to.
    Accessing from the domain that does not belong to them will result in 403_FORBIDDEN.
    """
    user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    response = client.get(f"/api/tenants/{tenant1.id}/", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == tenant1.id

    response = client.get(f"/api/tenants/{tenant2.id}/", format="json")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    client.defaults['HTTP_HOST'] = domain_url2

    response = client.get(f"/api/tenants/{tenant1.id}/", format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    response = client.get(f"/api/tenants/{tenant2.id}/", format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_other_users_tenant_retrival(client, tenant_setup):
    """
    Tenant users can only get tenant they belong to.
    Accessing from the domain that does not belong to them will result in 403_FORBIDDEN.
    """
    user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    response = client.get(f"/api/tenants/{tenant1.id}/", format="json")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client.get(f"/api/tenants/{tenant2.id}/", format="json")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    client.defaults['HTTP_HOST'] = domain_url2

    response = client.get(f"/api/tenants/{tenant1.id}/", format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    response = client.get(f"/api/tenants/{tenant2.id}/", format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN