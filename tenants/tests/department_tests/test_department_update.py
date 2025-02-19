import pytest
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN

from tenants.models import Department
from tenants.tests.conftest import get_access_token

@pytest.mark.django_db
def test_admin_department_update(client, tenant_setup):
    """
    Tenant admin can update any department, on any domain, using any department id, by using either PUT or PATCH methods.
    While organizations, could not change their tenant, departments can have their organization changed as long as they share tenant scope
    """
    admin_user = tenant_setup["users"]["admins"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]
    department1 = tenant_setup["departments"][organization1][0]
    department2 = tenant_setup["departments"][organization2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "Dept - PATCHED"}
    update_response = client.patch(f"/api/departments/{department1.id}/",data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == data.get("name")
    assert update_response.data["organization_id"] == organization1.id

    data = {"name": "Dept - UPDATED", "organization": organization2.id}

    update_response = client.put(f"/api/departments/{department1.id}/", data=data, format="json")

    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == data.get("name")
    assert update_response.data["organization_id"] == data.get("organization")
    assert update_response.data["organization_id"] != organization1.id

    client.defaults['HTTP_HOST'] = domain_url2

    data = {"name": "Dept - OVER_PATCHED"}
    update_response = client.patch(f"/api/departments/{department1.id}/", data=data, format="json")

    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == data.get("name")
    assert update_response.data["organization_id"] == organization2.id

    data = {"name": "Dept - OVER_UPDATED", "organization": organization1.id}
    update_response = client.put(f"/api/departments/{department1.id}/", data=data, format="json")

    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == data.get("name")
    assert update_response.data["organization_id"] == data.get("organization")
    assert update_response.data["organization_id"] != organization2.id


@pytest.mark.django_db
def test_tenant_user_department_update(client, tenant_setup):
    """
    Tenant user can update an department, on a domain belonging to their tenant, using organization id, by using either PUT or PATCH methods.
    While organizations, could not change their tenant, departments can have their organization change as long as they share tenant scope
    Additionally they are not allowed to modify organizations outside of their tenant scope.
    """
    tenant_user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]
    department1 = tenant_setup["departments"][organization1][0]
    department2 = tenant_setup["departments"][organization2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "Dept - PATCHED"}
    update_response = client.patch(f"/api/departments/{department1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == data.get("name")
    assert update_response.data["organization_id"] == organization1.local_id

    data = {"name": "Dept - OVER_UPDATED", "organization": organization2.local_id}
    update_response = client.put(f"/api/departments/{department1.local_id}/", data=data, format="json")

    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == data.get("name")
    assert update_response.data["organization_id"] == data.get("organization")
    assert update_response.data["organization_id"] == organization1.local_id
    assert organization2.local_id == organization1.local_id

    client.defaults['HTTP_HOST'] = domain_url2

    data = {"name": "Dept - RE_PATCHED"}
    update_response = client.patch(f"/api/departments/{department1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Dept - RE_PATCHED"}
    update_response = client.patch(f"/api/departments/{department2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    client.defaults['HTTP_HOST'] = domain_url1

    data = {"name": "Dept - RE_PATCHED"}
    update_response = client.patch(f"/api/departments/{department2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] != department2.name
    assert update_response.data["name"] == Department.objects.filter(local_id=department2.local_id, organization=organization1).first().name
    assert organization2.local_id == organization1.local_id


@pytest.mark.django_db
def test_organization_user_department_update(client, tenant_setup):
    """
    Organization user can update organization, as long as organization belongs to their scope.
    """
    organization_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]
    department1 = tenant_setup["departments"][organization1][0]
    department2 = tenant_setup["departments"][organization2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, organization_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "Dept - PATCHED"}
    update_response = client.patch(f"/api/departments/{department1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK

    data = {"name": "Dept - UPDATED", "organization": organization1.local_id}
    update_response = client.put(f"/api/departments/{department1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK

    data = {"name": "Dept - PATCHED"}
    update_response = client.patch(f"/api/departments/{department2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert department2.local_id == department1.local_id
    assert Department.objects.get(id=department2.id).name != data.get("name")

    data = {"name": "Dept - UPDATED", "organization": organization1.local_id}
    update_response = client.put(f"/api/departments/{department2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert Department.objects.get(id=department2.id).name != data.get("name")
    assert Department.objects.get(id=department2.id).organization != organization1

    client.defaults['HTTP_HOST'] = domain_url2

    data = {"name": "Dept - PATCHED"}
    update_response = client.patch(f"/api/departments/{department2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Dept - UPDATED", "organization": organization1.local_id}
    update_response = client.put(f"/api/departments/{department2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_department_user_department_update(client, tenant_setup):
    """
    Department user cannot update any department, they can only view department belonging to their scope.
    Since department users are only permitted viewing the department they belong to,
    any attempt to update any department will result in HTTP_403_FORBIDDEN
    """
    organization_user = tenant_setup["users"]["departments"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]
    department1 = tenant_setup["departments"][organization1][0]
    department2 = tenant_setup["departments"][organization2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, organization_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "Dept A - PATCHED"}
    update_response = client.patch(f"/api/departments/{department1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Dept A - UPDATED", "organization": organization1.local_id}
    update_response = client.put(f"/api/departments/{department1.id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Dept A - PATCHED"}
    update_response = client.patch(f"/api/departments/{department2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Dept A - UPDATED", "organization": organization1.local_id}
    update_response = client.put(f"/api/departments/{department2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    client.defaults['HTTP_HOST'] = domain_url2

    data = {"name": "Dept A - PATCHED"}
    update_response = client.patch(f"/api/departments/{department2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Dept A - UPDATED", "organization": organization1.local_id}
    update_response = client.put(f"/api/departments/{department2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_customer_user_department_update(client, tenant_setup):
    """
    Customer users cannot update any department,
    any attempt to update any department will result in HTTP_403_FORBIDDEN
    """
    organization_user = tenant_setup["users"]["customers"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]
    department1 = tenant_setup["departments"][organization1][0]
    department2 = tenant_setup["departments"][organization2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, organization_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "Dept A - PATCHED"}
    update_response = client.patch(f"/api/departments/{department1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Dept A - UPDATED", "organization": organization1.local_id}
    update_response = client.put(f"/api/departments/{department1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Dept A - PATCHED"}
    update_response = client.patch(f"/api/departments/{department2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Dept A - UPDATED", "organization": organization1.local_id}
    update_response = client.put(f"/api/departments/{department2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    client.defaults['HTTP_HOST'] = domain_url2

    data = {"name": "Dept A - PATCHED"}
    update_response = client.patch(f"/api/departments/{department2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Dept A - UPDATED", "organization": organization1.local_id}
    update_response = client.put(f"/api/departments/{department2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN