import pytest
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN

from tenants.tests.conftest import get_access_token


@pytest.mark.django_db
def test_admin_department_get(client, tenant_setup):
    """
    Tenant admin can get any department, on any domain, using any organization id, on any domain
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

    retrieve_response1 = client.get(f"/api/departments/{department1.id}/", format="json")
    assert retrieve_response1.status_code == HTTP_200_OK
    assert retrieve_response1.data["id"] == department1.id
    assert retrieve_response1.data["name"] == department1.name

    retrieve_response2 = client.get(f"/api/departments/{department2.id}/", format="json")
    assert retrieve_response2.status_code == HTTP_200_OK
    assert retrieve_response2.data["id"] == department2.id
    assert retrieve_response2.data["name"] == department2.name

    client.defaults['HTTP_HOST'] = domain_url2

    retrieve_response1 = client.get(f"/api/departments/{department1.id}/", format="json")
    assert retrieve_response1.status_code == HTTP_200_OK
    assert retrieve_response1.data["id"] == department1.id
    assert retrieve_response1.data["name"] == department1.name

    retrieve_response2 = client.get(f"/api/departments/{department2.id}/", format="json")
    assert retrieve_response2.status_code == HTTP_200_OK
    assert retrieve_response2.data["id"] == department2.id
    assert retrieve_response2.data["name"] == department2.name


@pytest.mark.django_db
def test_tenant_user_department_get(client, tenant_setup):
    """
    Tenant user can get an department, on domain that belongs to their tenant scope, using department id
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

    retrieve_response1 = client.get(f"/api/departments/{department1.local_id}/", format="json")

    assert retrieve_response1.status_code == HTTP_200_OK

    retrieved_org = retrieve_response1.data

    assert retrieved_org["id"] == department1.local_id
    assert retrieved_org["name"] == department1.name


@pytest.mark.django_db
def test_tenant_user_department_get_department_created_on_different_domain(client, tenant_setup):
    """
    Tenant user cannot get department, created on domain that does not belong to their tenant scope
    Since they are using local_id, and not actual id, they will access department in their scope with that local_id
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

    retrieve_response1 = client.get(f"/api/departments/{department2.local_id}/", format="json")

    assert retrieve_response1.data.get("name") != department2.name


@pytest.mark.django_db
def test_tenant_user_department_get_mismatched_tenant(client, tenant_setup):
    """
    Tenant user cannot get department, created on domain that does not belong to their tenant scope,
    even if they access the api from the domain used when creating that department.
    In other words, they are forbidden from getting a department outside from their tenant scope
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

    client.defaults['HTTP_HOST'] = domain_url2

    retrieve_response1 = client.get(f"/api/departments/{department2.local_id}/", format="json")

    assert retrieve_response1.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_organization_user_department_get(client, tenant_setup):
    """
    Organization user can get departments, but only those created in their organization scope
    """
    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]
    department1 = tenant_setup["departments"][organization1][0]
    departmentA = tenant_setup["departments"][organization1][1]
    department2 = tenant_setup["departments"][organization2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response = client.get(f"/api/departments/{department1.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") == department1.name

    retrieve_response = client.get(f"/api/departments/{departmentA.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") == departmentA.name

    retrieve_response = client.get(f"/api/departments/{department2.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") != department2.name


@pytest.mark.django_db
def test_department_user_department_get(client, tenant_setup):
    """
    Department user can get department, but only the one they are associated with.
    """
    org_user = tenant_setup["users"]["departments"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]
    department1 = tenant_setup["departments"][organization1][0]
    departmentA = tenant_setup["departments"][organization1][1]
    department2 = tenant_setup["departments"][organization2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response = client.get(f"/api/departments/{department1.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") == department1.name
    assert retrieve_response.data.get("organization_id") == org_user.organization_scope.local_id

    retrieve_response = client.get(f"/api/departments/{departmentA.local_id}/", format="json")
    assert retrieve_response.status_code == HTTP_404_NOT_FOUND

    retrieve_response = client.get(f"/api/departments/{department2.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") != department2.name
    assert retrieve_response.data.get("name") == department1.name
    assert retrieve_response.data.get("organization_id") == org_user.organization_scope.local_id


@pytest.mark.django_db
def test_customer_user_department_get(client, tenant_setup):
    """
    Customer user cannot get department, even if they belong to that department.
    """
    customer_user = tenant_setup["users"]["customers"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    department1 = tenant_setup["departments"][organization1][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, customer_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response = client.get(f"/api/departments/{department1.id}/", format="json")

    assert retrieve_response.status_code == HTTP_404_NOT_FOUND