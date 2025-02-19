import pytest
from rest_framework import status
from tenants.models import Organization, Tenant, Domain
from tenants.tests.conftest import get_access_token


@pytest.mark.django_db
def test_admin_tenant_delete(client, tenant_setup):
    """
    Tenant admin can hard delete tenants
    Tenant deletion will also cause, domain to become inaccessible,
    and performing any requests on it will result in HTTP_403_FORBIDDEN
    """
    admin_user = tenant_setup["users"]["admins"][0]
    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/tenants/", format="json")

    assert list_response.status_code == status.HTTP_200_OK
    assert len(list_response.data) == Tenant.objects.all().count()

    response = client.delete(f"/api/tenants/{tenant1.id}/", format="json")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    list_response = client.get(f"/api/tenants/", format="json")

    assert list_response.status_code == status.HTTP_403_FORBIDDEN


    client.defaults['HTTP_HOST'] = domain_url2

    access_token = get_access_token(client, domain_url2, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/tenants/", format="json")

    assert list_response.status_code == status.HTTP_200_OK
    assert len(list_response.data) == Tenant.objects.all().count()

    response = client.delete(f"/api/tenants/{tenant2.id}/", format="json")

    assert response.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.django_db
def test_other_users_tenant_delete(client, tenant_setup):
    """
        Tenant admin can hard delete tenants
        """
    user = tenant_setup["users"]["tenants"][0]
    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    response = client.delete(f"/api/tenants/{tenant1.id}/", format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN

