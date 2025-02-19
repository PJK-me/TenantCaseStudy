import pytest
from rest_framework import status
from tenants.models import Organization, Department
from tenants.tests.conftest import get_access_token


@pytest.mark.django_db
def test_admin_department_create(client, tenant_setup):
    """
    Tenant admin can create a department, on any domain
    """
    admin_user = tenant_setup["users"]["admins"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url = tenant_setup["domains"][tenant1].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]

    client.defaults['HTTP_HOST'] = domain_url

    access_token = get_access_token(client, domain_url, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    dept_data = {"name": "Dept A", "organization": organization1.id}
    dept_response = client.post("/api/departments/", dept_data, format="json")

    assert dept_response.status_code == status.HTTP_201_CREATED
    assert dept_response.json()["name"] == dept_data.get("name")

    dept_id = dept_response.json()["id"]

    created_dept = Department.objects.get(id=dept_id)
    assert created_dept.organization.id == organization1.id


@pytest.mark.django_db
def test_tenant_user_department_create(client, tenant_setup):
    """
    Tenant user can create department, on domain inside their scope
    """

    tenant_user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]

    assert tenant_user.tenant_scope == tenant1

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    dept_data = {"name": "Dept A", "organization": organization1.local_id}
    dept_response = client.post("/api/departments/", dept_data, format="json")

    assert dept_response.status_code == status.HTTP_201_CREATED
    assert dept_response.json()["name"] == dept_data.get("name")

    dept_id = dept_response.json()["id"]

    created_dept = Department.objects.get(local_id=dept_id, organization__tenant=tenant_user.tenant_scope)
    assert created_dept.organization.id == organization1.id


@pytest.mark.django_db
def test_tenant_user_department_create_with_mismatched_tenant(client, tenant_setup):
    """
    Tenant users cannot create new departments, on domains outside their tenant scope.
    """
    tenant_user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    client.defaults['HTTP_HOST'] = domain_url2

    dept_data = {"name": "Dept A", "organization": organization1.local_id}
    dept_response = client.post("/api/departments/", dept_data, format="json")

    assert dept_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_organization_user_department_create(client, tenant_setup):
    """
    Organization users can create department, on domain inside their scope, however only associated with their organization scope.
    """
    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant1][1]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    dept_data = {"name": "Dept A", "organization": organization1.local_id}
    dept_response = client.post("/api/departments/", dept_data, format="json")

    assert dept_response.status_code == status.HTTP_201_CREATED
    assert dept_response.json()["name"] == dept_data.get("name")

    dept_id = dept_response.json()["id"]

    created_dept = Department.objects.get(local_id=dept_id, organization=org_user.organization_scope)
    assert created_dept.organization.id == organization1.id

    dept_data = {"name": "Dept B", "organization": organization2.local_id}
    dept_response = client.post("/api/departments/", dept_data, format="json")

    assert dept_response.status_code == status.HTTP_403_FORBIDDEN

    dept_data = {"name": "Dept B", "organization": 999}
    dept_response = client.post("/api/departments/", dept_data, format="json")

    assert dept_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_organization_user_department_create_using_out_of_scope_organization(client, tenant_setup):
    """
    Organization users cannot create department, on domain inside their scope, if they provide organization id outside of their scope
    This is due to data isolation, they cannot reference organization2, or even see its actual id (only local_id)
    """
    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][1]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    dept_data = {"name": "Dept A", "organization": organization2.local_id}
    dept_response = client.post("/api/departments/", dept_data, format="json")

    assert dept_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_department_user_department_create(client, tenant_setup):
    """
    Department users cannot create department
    """
    department_user = tenant_setup["users"]["departments"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][1]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, department_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    dept_data = {"name": "Dept A", "organization": organization1.local_id}
    dept_response = client.post("/api/departments/", dept_data, format="json")

    assert dept_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_customer_user_department_create(client, tenant_setup):
    """
    Customer users cannot create department
    """
    customer_user = tenant_setup["users"]["customers"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][1]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, customer_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    dept_data = {"name": "Dept A", "organization": organization1.local_id}
    dept_response = client.post("/api/departments/", dept_data, format="json")

    assert dept_response.status_code == status.HTTP_403_FORBIDDEN
