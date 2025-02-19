import pytest
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN

from tenants.tests.conftest import get_access_token

@pytest.mark.django_db
def test_admin_organization_update(client, tenant_setup):
    """
    Tenant admin can update an organization, on any domain, using any organization id, by using either PUT or PATCH methods.
    However data isolation does not allow admin to change the tenant of organization when using PUT method
    Other fields will be updated, but tenant will remain unchanged.
    """
    admin_user = tenant_setup["users"]["admins"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    org_data = {"name": "Org A - PATCHED"}
    update_response = client.patch(f"/api/organizations/{organization1.id}/",data=org_data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == org_data.get("name")
    assert update_response.data["tenant_id"] == tenant1.id

    org_data = {"name": "Org A - UPDATED", "tenant": tenant2.id}

    update_response = client.put(f"/api/organizations/{organization1.id}/", data=org_data, format="json")

    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == org_data.get("name")
    assert update_response.data["tenant_id"] != org_data.get("tenant")
    assert update_response.data["tenant_id"] == tenant1.id

    client.defaults['HTTP_HOST'] = domain_url2

    org_data = {"name": "Org A - OVER_PATCHED"}
    update_response = client.patch(f"/api/organizations/{organization1.id}/", data=org_data, format="json")

    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == org_data.get("name")
    assert update_response.data["tenant_id"] == tenant1.id

    org_data = {"name": "Org A - OVER_UPDATED", "tenant": tenant2.id}
    update_response = client.put(f"/api/organizations/{organization1.id}/", data=org_data, format="json")

    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == org_data.get("name")
    assert update_response.data["tenant_id"] != org_data.get("tenant")
    assert update_response.data["tenant_id"] == tenant1.id

@pytest.mark.django_db
def test_tenant_user_organization_update(client, tenant_setup):
    """
    Tenant user can update an organization, on a domain belonging to their tenant, using organization id, by using either PUT or PATCH methods.
    However data isolation does not allow tenant user to change the tenant of organization when using PUT method
    Other fields will be updated, but tenant will remain unchanged.
    Additionally they are not allowed to modify organizations outside of their tenant scope.
    """
    tenant_user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    org_data = {"name": "Org A - PATCHED"}
    update_response = client.patch(f"/api/organizations/{organization1.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == org_data.get("name")
    assert update_response.data["tenant_id"] == tenant1.id

    org_data = {"name": "Org A - OVER_UPDATED", "tenant": tenant2.id}
    update_response = client.put(f"/api/organizations/{organization1.local_id}/", data=org_data, format="json")

    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == org_data.get("name")
    assert update_response.data["tenant_id"] != org_data.get("tenant")
    assert update_response.data["tenant_id"] == tenant1.id

    client.defaults['HTTP_HOST'] = domain_url2

    org_data = {"name": "Org A - RE_PATCHED"}
    update_response = client.patch(f"/api/organizations/{organization1.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    org_data = {"name": "Org A - RE_PATCHED"}
    update_response = client.patch(f"/api/organizations/{organization2.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    client.defaults['HTTP_HOST'] = domain_url1

    org_data = {"name": "Org A - RE_PATCHED"}
    update_response = client.patch(f"/api/organizations/{organization2.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] != organization2.name
    assert update_response.data["name"] == org_data.get("name")


@pytest.mark.django_db
def test_organization_user_organization_update(client, tenant_setup):
    """
    Organization user cannot update any organization, they can only view organization belonging to their scope.
    Since organization users are only permitted viewing the organization they belong to,
    any attempt to update any organization will result in HTTP_403_FORBIDDEN
    """
    organization_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, organization_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    org_data = {"name": "Org A - PATCHED"}
    update_response = client.patch(f"/api/organizations/{organization1.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    org_data = {"name": "Org A - UPDATED", "tenant": tenant1.local_id}
    update_response = client.put(f"/api/organizations/{organization1.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    org_data = {"name": "Org A - PATCHED"}
    update_response = client.patch(f"/api/organizations/{organization2.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    org_data = {"name": "Org A - UPDATED", "tenant": tenant1.local_id}
    update_response = client.put(f"/api/organizations/{organization2.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    client.defaults['HTTP_HOST'] = domain_url2

    org_data = {"name": "Org A - PATCHED"}
    update_response = client.patch(f"/api/organizations/{organization2.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    org_data = {"name": "Org A - UPDATED", "tenant": tenant1.local_id}
    update_response = client.put(f"/api/organizations/{organization2.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_customer_user_organization_update(client, tenant_setup):
    """
    Customer user cannot update any organization. Any attempt to do so will result in HTTP_403_FORBIDDEN.
    """
    organization_user = tenant_setup["users"]["customers"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, organization_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    org_data = {"name": "Org A - PATCHED"}
    update_response = client.patch(f"/api/organizations/{organization1.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    org_data = {"name": "Org A - UPDATED", "tenant": tenant1.local_id}
    update_response = client.put(f"/api/organizations/{organization1.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    org_data = {"name": "Org A - PATCHED"}
    update_response = client.patch(f"/api/organizations/{organization2.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    org_data = {"name": "Org A - UPDATED", "tenant": tenant1.local_id}
    update_response = client.put(f"/api/organizations/{organization2.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    client.defaults['HTTP_HOST'] = domain_url2

    org_data = {"name": "Org A - PATCHED"}
    update_response = client.patch(f"/api/organizations/{organization2.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    org_data = {"name": "Org A - UPDATED", "tenant": tenant1.local_id}
    update_response = client.put(f"/api/organizations/{organization2.local_id}/", data=org_data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN
