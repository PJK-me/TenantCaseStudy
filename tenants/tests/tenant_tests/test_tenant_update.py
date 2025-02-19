import pytest
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST

from tenants.models import Tenant, Domain
from tenants.tests.conftest import get_access_token

@pytest.mark.django_db
def test_admin_tenant_update(client, tenant_setup):
    """
    Tenant admin can modify tenants, alongside the domain url
    """
    admin_user = tenant_setup["users"]["admins"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain1 = tenant_setup["domains"][tenant1]
    domain_url1 = domain1.domain_url
    domain2 = tenant_setup["domains"][tenant2]
    domain_url2 = domain2.domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "Tenant - PATCHED"}
    update_response = client.patch(f"/api/tenants/{tenant1.id}/",data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == data.get("name")
    assert Tenant.objects.get(id=tenant1.id).domain.id == domain1.id


    data = {"name": "Tenant - UPDATED", "domain_url": "new_tenant.example.com"}
    update_response = client.put(f"/api/tenants/{tenant2.id}/", data=data, format="json")

    assert update_response.status_code == HTTP_200_OK
    assert Tenant.objects.get(id=tenant2.id).domain.domain_url == data.get("domain_url")


def test_other_users_tenant_update(client, tenant_setup):
    """
    Other users cannot modify tenants
    """
    user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain1 = tenant_setup["domains"][tenant1]
    domain_url1 = domain1.domain_url
    domain2 = tenant_setup["domains"][tenant2]
    domain_url2 = domain2.domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "Tenant - PATCHED"}
    update_response = client.patch(f"/api/tenants/{tenant1.id}/",data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Tenant - UPDATED", "domain_url": "new_tenant.example.com"}
    update_response = client.put(f"/api/tenants/{tenant2.id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN



    