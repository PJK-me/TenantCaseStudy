import pytest
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN

from tenants.tests.conftest import get_access_token


@pytest.mark.django_db
def test_admin_customer_get(client, tenant_setup):
    """
    Tenant admin can get any customer, on any domain, using any customer id, on any domain
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
    customer1 = tenant_setup["customers"][department1][0]
    customer2 = tenant_setup["customers"][department2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response1 = client.get(f"/api/customers/{customer1.id}/", format="json")
    assert retrieve_response1.status_code == HTTP_200_OK
    assert retrieve_response1.data["id"] == customer1.id
    assert retrieve_response1.data["name"] == customer1.name

    retrieve_response2 = client.get(f"/api/customers/{customer2.id}/", format="json")
    assert retrieve_response2.status_code == HTTP_200_OK
    assert retrieve_response2.data["id"] == customer2.id
    assert retrieve_response2.data["name"] == customer2.name

    client.defaults['HTTP_HOST'] = domain_url2

    retrieve_response1 = client.get(f"/api/customers/{customer1.id}/", format="json")
    assert retrieve_response1.status_code == HTTP_200_OK
    assert retrieve_response1.data["id"] == customer1.id
    assert retrieve_response1.data["name"] == customer1.name

    retrieve_response2 = client.get(f"/api/customers/{customer2.id}/", format="json")
    assert retrieve_response2.status_code == HTTP_200_OK
    assert retrieve_response2.data["id"] == customer2.id
    assert retrieve_response2.data["name"] == customer2.name


@pytest.mark.django_db
def test_tenant_user_customer_get(client, tenant_setup):
    """
    Tenant user can get any customer, on domain that belongs to their tenant scope, using customer local_id
    Due to data isolation, its impossible for them to access other customers, since non-admin users use local_id
    for customer instances
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
    customer1 = tenant_setup["customers"][department1][0]
    customer2 = tenant_setup["customers"][department2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response1 = client.get(f"/api/customers/{customer1.local_id}/", format="json")

    assert retrieve_response1.status_code == HTTP_200_OK

    retrieved_org = retrieve_response1.data

    assert retrieved_org["id"] == customer1.local_id
    assert retrieved_org["name"] == customer1.name


@pytest.mark.django_db
def test_tenant_user_customer_get_customer_created_on_different_domain(client, tenant_setup):
    """
    Tenant user cannot get a customer, created on domain that does not belong to their tenant scope
    They are limited to their own scope
    In this case api returns customer instance with the same local_id as customer in their scope
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
    customer1 = tenant_setup["customers"][department1][0]
    customer2 = tenant_setup["customers"][department2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response1 = client.get(f"/api/customers/{customer2.local_id}/", format="json")

    assert retrieve_response1.status_code == HTTP_200_OK
    assert retrieve_response1.data.get("name") != customer2.name
    assert retrieve_response1.data.get("name") == customer1.name


@pytest.mark.django_db
def test_tenant_user_customer_get_mismatched_tenant(client, tenant_setup):
    """
    Tenant user cannot get a customer, created on domain that does not belong to their tenant scope,
    even if they access the api from the domain used when creating that customer.
    In other words, they are forbidden from getting a customer outside from their tenant scope
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
    customer1 = tenant_setup["customers"][department1][0]
    customer2 = tenant_setup["customers"][department2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    client.defaults['HTTP_HOST'] = domain_url2

    retrieve_response1 = client.get(f"/api/customers/{customer2.local_id}/", format="json")

    assert retrieve_response1.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_organization_user_customer_get(client, tenant_setup):
    """
    Organization user can get customers, but only those created in their organization scope
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
    customer1 = tenant_setup["customers"][department1][0]
    customerA = tenant_setup["customers"][department1][1]
    customer2 = tenant_setup["customers"][department2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response = client.get(f"/api/customers/{customer1.local_id}/", format="json")
    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") == customer1.name

    retrieve_response = client.get(f"/api/customers/{customerA.local_id}/", format="json")
    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") == customerA.name

    retrieve_response = client.get(f"/api/customers/{customer2.local_id}/", format="json")
    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") != customer2.name
    assert customer1.local_id == customer2.local_id


@pytest.mark.django_db
def test_department_user_customer_get(client, tenant_setup):
    """
    Department user can get customers, but only those created in their department scope
    """
    dept_user = tenant_setup["users"]["departments"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]
    department1 = tenant_setup["departments"][organization1][0]
    departmentA = tenant_setup["departments"][organization1][1]
    department2 = tenant_setup["departments"][organization2][0]
    customer1 = tenant_setup["customers"][department1][0]
    customerA = tenant_setup["customers"][department1][1]
    customer2 = tenant_setup["customers"][department2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, dept_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response = client.get(f"/api/customers/{customer1.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") == customer1.name
    assert retrieve_response.data.get("department_id") == customer1.department.local_id
    assert retrieve_response.data.get("department_id") == dept_user.department_scope.local_id

    retrieve_response = client.get(f"/api/customers/{customerA.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") == customerA.name
    assert retrieve_response.data.get("department_id") == customer1.department.local_id
    assert retrieve_response.data.get("department_id") == dept_user.department_scope.local_id

    retrieve_response = client.get(f"/api/customers/{customer2.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") != customer2.name


@pytest.mark.django_db
def test_customer_user_customer_get(client, tenant_setup):
    """
    Customer user can get customer, but only the one they are associated with.
    """
    org_user = tenant_setup["users"]["customers"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]
    department1 = tenant_setup["departments"][organization1][0]
    department2 = tenant_setup["departments"][organization2][0]
    customer1 = tenant_setup["customers"][department1][0]
    customerA = tenant_setup["customers"][department1][1]
    customer2 = tenant_setup["customers"][department2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response = client.get(f"/api/customers/{customer1.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") == customer1.name

    retrieve_response = client.get(f"/api/customers/{customerA.local_id}/", format="json")
    assert retrieve_response.status_code == HTTP_404_NOT_FOUND

    retrieve_response = client.get(f"/api/customers/{customer2.local_id}/", format="json")
    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") != customer2.name
    assert retrieve_response.data.get("name") == customer1.name