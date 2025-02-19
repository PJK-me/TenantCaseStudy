import pytest
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN

from tenants.models import Organization, Tenant
from tenants.tests.conftest import get_access_token



@pytest.mark.django_db
def test_admin_tenant_list(client, tenant_setup):
    """
    Tenant admin can list all tenants, on any domain
    """
    admin_user = tenant_setup["users"]["admins"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    all_tenants_count = Tenant.objects.all().count()

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/tenants/", format="json")
    assert len(list_response.data) == all_tenants_count

    client.defaults['HTTP_HOST'] = domain_url2

    list_response = client.get(f"/api/tenants/", format="json")
    assert len(list_response.data) == all_tenants_count


@pytest.mark.django_db
def test_tenant_user_tenant_list(client, tenant_setup):
    """
    Tenant users can list only single tenant they belong to.
    Additionally they can only access it using domain they belong to.
    """
    tenant_user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/tenants/", format="json")
    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 1
    assert list_response.data[0]["id"] == tenant1.id

    client.defaults['HTTP_HOST'] = domain_url2

    list_response = client.get(f"/api/tenants/", format="json")
    assert list_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_other_users_tenant_list(client, tenant_setup):
    """
    Other users cannot list tenants
    """
    tenant_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/tenants/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 0

    client.defaults['HTTP_HOST'] = domain_url2

    list_response = client.get(f"/api/tenants/", format="json")
    assert list_response.status_code == HTTP_403_FORBIDDEN


