import pytest
from rest_framework import status
from tenants.models import Organization, Department, Customer
from tenants.tests.conftest import get_access_token


@pytest.mark.django_db
def test_admin_customer_create(client, tenant_setup):
    """
    Tenant admin can create a customer, on any domain
    """
    admin_user = tenant_setup["users"]["admins"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url = tenant_setup["domains"][tenant1].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    department1 = tenant_setup["departments"][organization1][0]

    client.defaults['HTTP_HOST'] = domain_url

    access_token = get_access_token(client, domain_url, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    customer_data = {"name": "Customer A", "department": department1.id}
    customer_response = client.post("/api/customers/", customer_data, format="json")

    assert customer_response.status_code == status.HTTP_201_CREATED
    assert customer_response.json()["name"] == customer_data.get("name")

    customer_id = customer_response.json()["id"]

    created_customer = Customer.objects.get(id=customer_id)
    assert created_customer.department.id == department1.id


@pytest.mark.django_db
def test_tenant_user_customer_create(client, tenant_setup):
    """
    Tenant user can create customer, on domain inside their scope
    """

    tenant_user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    department1 = tenant_setup["departments"][organization1][0]

    assert tenant_user.tenant_scope == tenant1

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    customer_data = {"name": "Customer A", "department": department1.local_id}
    customer_response = client.post("/api/customers/", customer_data, format="json")

    assert customer_response.status_code == status.HTTP_201_CREATED
    assert customer_response.json()["name"] == customer_data.get("name")

    customer_id = customer_response.json()["id"]

    created_customer = Customer.objects.get(local_id=customer_id, department__organization__tenant=tenant_user.tenant_scope)
    assert created_customer.department.id == department1.id


@pytest.mark.django_db
def test_organization_user_customer_create(client, tenant_setup):
    """
    Organization users can create customer, on domain inside their scope, however only associated with their organization scope.
    """
    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant1][1]
    department1 = tenant_setup["departments"][organization1][0]
    department2 = tenant_setup["departments"][organization2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    customer_data = {"name": "Customer A", "department": department1.local_id}
    customer_response = client.post("/api/customers/", customer_data, format="json")

    assert customer_response.status_code == status.HTTP_201_CREATED
    assert customer_response.json()["name"] == customer_data.get("name")

    customer_id = customer_response.json()["id"]

    created_customer = Customer.objects.get(local_id=customer_id, department__organization=org_user.organization_scope)
    assert created_customer.department.id == department1.id

    customer_data = {"name": "Customer A", "department": department2.local_id}
    customer_response = client.post("/api/customers/", customer_data, format="json")

    assert customer_response.status_code == status.HTTP_403_FORBIDDEN

    customer_data = {"name": "Customer A", "department": 999}
    customer_response = client.post("/api/customers/", customer_data, format="json")

    assert customer_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_organization_user_customer_create_using_out_of_scope_organization(client, tenant_setup):
    """
    Organization users cannot create customer, on domain inside their scope, if they provide department id outside of their scope
    because its impossible for them to provide an id outside ot their scope
    """
    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][1]
    department1 = tenant_setup["departments"][organization1][0]
    department2 = tenant_setup["departments"][organization2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    assert org_user.organization_scope == organization1
    assert org_user.organization_scope != organization2

    assert department1.id != department2.id
    assert department1.local_id != department2.local_id
    assert department1.organization != department2.organization

    customer_data = {"name": "Customer A", "department": department2.local_id}
    customer_response = client.post("/api/customers/", customer_data, format="json")

    assert customer_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_department_user_customer_create(client, tenant_setup):
    """
    Department users can create customer, on domain inside their scope, however only associated with their organization scope.
    """
    department_user = tenant_setup["users"]["departments"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][1]
    department1 = tenant_setup["departments"][organization1][0]
    departmentA = tenant_setup["departments"][organization1][1]
    department2 = tenant_setup["departments"][organization2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, department_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    customer_data = {"name": "Customer A", "department": department1.local_id}
    customer_response = client.post("/api/customers/", customer_data, format="json")

    assert customer_response.status_code == status.HTTP_201_CREATED
    assert customer_response.json()["name"] == customer_data.get("name")

    customer_id = customer_response.json()["id"]

    created_customer = Customer.objects.get(local_id=customer_id, department=department_user.department_scope)
    assert created_customer.department.id == department1.id

    customer_data = {"name": "Customer B", "department": departmentA.local_id}
    customer_response = client.post("/api/customers/", customer_data, format="json")

    assert customer_response.status_code == status.HTTP_403_FORBIDDEN

    customer_data = {"name": "Customer C", "department": department2.local_id}
    customer_response = client.post("/api/customers/", customer_data, format="json")

    assert customer_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_customer_user_customer_create(client, tenant_setup):
    """
    Customer users cannot create customer
    """
    customer_user = tenant_setup["users"]["customers"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][1]
    department1 = tenant_setup["departments"][organization1][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, customer_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    customer_data = {"name": "Customer A", "department": department1.id}
    customer_response = client.post("/api/customers/", customer_data, format="json")

    assert customer_response.status_code == status.HTTP_403_FORBIDDEN
