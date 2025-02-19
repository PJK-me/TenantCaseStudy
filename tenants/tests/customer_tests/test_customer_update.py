import pytest
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN

from tenants.models import Department, Customer
from tenants.tests.conftest import get_access_token

@pytest.mark.django_db
def test_admin_organization_update(client, tenant_setup):
    """
    Tenant admin can update any customer, on any domain, using any customer id, by using either PUT or PATCH methods.
    While organizations, could not change their tenant, customers can have their department changed as long as they share tenant scope
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

    data = {"name": "Customer - PATCHED"}
    update_response = client.patch(f"/api/customers/{customer1.id}/",data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == data.get("name")
    assert update_response.data["department_id"] == department1.id

    data = {"name": "Customer - UPDATED", "department": department2.id}

    update_response = client.put(f"/api/customers/{customer1.id}/", data=data, format="json")

    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == data.get("name")
    assert update_response.data["department_id"] == data.get("department")
    assert update_response.data["department_id"] != department1.id

    client.defaults['HTTP_HOST'] = domain_url2

    data = {"name": "Customer - OVER_PATCHED"}
    update_response = client.patch(f"/api/customers/{customer1.id}/", data=data, format="json")

    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == data.get("name")
    assert update_response.data["department_id"] == department2.id

    data = {"name": "Customer - OVER_UPDATED", "department": department1.id}
    update_response = client.put(f"/api/customers/{customer1.id}/", data=data, format="json")

    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == data.get("name")
    assert update_response.data["department_id"] == data.get("department")
    assert update_response.data["department_id"] != department2.id


@pytest.mark.django_db
def test_tenant_user_customer_update(client, tenant_setup):
    """
    Tenant user can update an customer, on a domain belonging to their tenant, using customer id, by using either PUT or PATCH methods.
    While organizations, could not change their tenant, customer can have their department changed as long as they share tenant scope
    Additionally they are not allowed to modify departments outside of their tenant scope.
    In this case when we try to change our customer department - we actually access department1 not department2 instance
    Thats because those two departments are in seperate tenant scopes - and they share local_id
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

    data = {"name": "Customer - PATCHED"}
    update_response = client.patch(f"/api/customers/{customer1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == data.get("name")
    assert update_response.data["department_id"] == department1.local_id

    data = {"name": "Customer - OVER_UPDATED", "department": department2.local_id}
    update_response = client.put(f"/api/customers/{customer1.local_id}/", data=data, format="json")

    assert update_response.status_code == HTTP_200_OK
    assert update_response.data["name"] == data.get("name")
    assert update_response.data["name"] == Customer.objects.get(id=customer1.id).name
    assert update_response.data["department_id"] == data.get("department")
    assert update_response.data["department_id"] == department2.local_id
    assert Customer.objects.get(id=customer1.id).department.id != department2.id
    assert Customer.objects.get(id=customer1.id).department.id == department1.id

    client.defaults['HTTP_HOST'] = domain_url2

    data = {"name": "Customer - RE_PATCHED"}
    update_response = client.patch(f"/api/customers/{customer1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Customer - RE_PATCHED"}
    update_response = client.patch(f"/api/customers/{customer2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    client.defaults['HTTP_HOST'] = domain_url1

    data = {"name": "Customer - RE_PATCHED"}
    update_response = client.patch(f"/api/customers/{customer2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert Customer.objects.get(id=customer2.id).name != data.get("name")
    assert Customer.objects.get(id=customer1.id).name == data.get("name")
    assert customer2.local_id == customer1.local_id


@pytest.mark.django_db
def test_organization_user_customer_update(client, tenant_setup):
    """
    Organization user can update customers, as long as organization belongs to their scope.
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
    customer1 = tenant_setup["customers"][department1][0]
    customer2 = tenant_setup["customers"][department2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, organization_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "Customer - PATCHED"}
    update_response = client.patch(f"/api/customers/{customer1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert Customer.objects.get(id=customer1.id).name == data.get("name")

    data = {"name": "Customer - UPDATED", "department": department1.local_id}
    update_response = client.put(f"/api/customers/{customer1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert Customer.objects.get(id=customer1.id).name == data.get("name")
    assert Customer.objects.get(id=customer1.id).department.id == department1.id

    data = {"name": "Customer - PATCHED"}
    update_response = client.patch(f"/api/customers/{customer2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert Customer.objects.get(id=customer2.id).name != data.get("name")
    assert Customer.objects.get(id=customer1.id).name == data.get("name")


    data = {"name": "Customer - UPDATED", "department": department1.local_id}
    update_response = client.put(f"/api/customers/{customer2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert Customer.objects.get(id=customer2.id).name != data.get("name")
    assert Customer.objects.get(id=customer1.id).name == data.get("name")
    assert Customer.objects.get(id=customer2.id).department.id != department1.id
    assert Customer.objects.get(id=customer1.id).department.id == department1.id

    client.defaults['HTTP_HOST'] = domain_url2

    data = {"name": "Customer - PATCHED"}
    update_response = client.patch(f"/api/customers/{customer2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Customer - UPDATED", "department": department1.local_id}
    update_response = client.put(f"/api/customers/{customer2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_department_user_customer_update(client, tenant_setup):
    """
    Department users can update customers, as long as they belong to users department scope
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
    customer1 = tenant_setup["customers"][department1][0]
    customer2 = tenant_setup["customers"][department2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, organization_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "Customer A - PATCHED"}
    update_response = client.patch(f"/api/customers/{customer1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert Customer.objects.get(id=customer1.id).name == data.get("name")

    data = {"name": "Customer A - UPDATED", "department": department1.local_id}
    update_response = client.put(f"/api/customers/{customer1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert Customer.objects.get(id=customer1.id).name == data.get("name")
    assert Customer.objects.get(id=customer1.id).department.id == department1.id

    data = {"name": "Customer A - PATCHED"}
    update_response = client.patch(f"/api/customers/{customer2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert Customer.objects.get(id=customer2.id).name != data.get("name")
    assert Customer.objects.get(id=customer1.id).name == data.get("name")

    data = {"name": "Customer A - UPDATED", "department": department1.local_id}
    update_response = client.put(f"/api/customers/{customer2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_200_OK
    assert Customer.objects.get(id=customer2.id).name != data.get("name")
    assert Customer.objects.get(id=customer1.id).name == data.get("name")
    assert Customer.objects.get(id=customer2.id).department.id != department1.id
    assert Customer.objects.get(id=customer1.id).department.id == department1.id

    client.defaults['HTTP_HOST'] = domain_url2

    data = {"name": "Customer A - PATCHED"}
    update_response = client.patch(f"/api/customers/{customer2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Customer A - UPDATED", "department": department1.local_id}
    update_response = client.put(f"/api/customers/{customer2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_customer_user_customer_update(client, tenant_setup):
    """
    Customer user cannot update any customer, they can only view customer belonging to their scope.
    Since customer users are only permitted viewing the customer they belong to,
    any attempt to update any customer will result in HTTP_403_FORBIDDEN
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
    customer1 = tenant_setup["customers"][department1][0]
    customer2 = tenant_setup["customers"][department2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, organization_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    data = {"name": "Customer A - PATCHED"}
    update_response = client.patch(f"/api/customers/{customer1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Customer A - UPDATED", "department": department1.local_id}
    update_response = client.put(f"/api/customers/{customer1.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Customer A - PATCHED"}
    update_response = client.patch(f"/api/customers/{customer2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Customer A - UPDATED", "department": department1.local_id}
    update_response = client.put(f"/api/customers/{customer2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    client.defaults['HTTP_HOST'] = domain_url2

    data = {"name": "Customer A - PATCHED"}
    update_response = client.patch(f"/api/customers/{customer2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN

    data = {"name": "Customer A - UPDATED", "department": department1.local_id}
    update_response = client.put(f"/api/customers/{customer2.local_id}/", data=data, format="json")
    assert update_response.status_code == HTTP_403_FORBIDDEN


