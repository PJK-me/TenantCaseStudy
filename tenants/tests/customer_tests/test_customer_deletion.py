import pytest
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_204_NO_CONTENT, \
    HTTP_401_UNAUTHORIZED

from tenants.models import Organization, Department, Customer
from tenants.tests.conftest import get_access_token
from django.urls import reverse

def get_token_response(client, domain, username):
    client.defaults['HTTP_HOST'] = domain

    token_response = client.post(reverse('token_obtain_pair'), {
        "username": username,
        "password": "password"
    }, format="json")

    return token_response



@pytest.mark.django_db
def test_admin_customer_delete(client, tenant_setup):
    """
    Tenant admin can hard delete any customer, on any domain, using any customer id
    Only tenant admin or superusers are capable of true deletion.
    Deletion will cascade removing all related instances of other models.
    Any other user permitted to delete customer will perform a soft deletion
    field is_deleted will be set to True, excluding it from querysets.
    Tenant admins and superusers will be able to see customers that were soft deleted.
    """
    admin_user = tenant_setup["users"]["admins"][0]
    customer_user = tenant_setup["users"]["customers"][0]
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

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Customer.objects.all().count()

    assert Customer.objects.filter(id=customer1.id).exists()

    delete_response = client.delete(f"/api/customers/{customer1.id}/", format="json")

    assert delete_response.status_code == HTTP_204_NO_CONTENT

    assert not Customer.objects.filter(id=customer1.id).exists()

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Customer.objects.all().count()

    client.defaults['HTTP_HOST'] = domain_url2

    assert Customer.objects.filter(id=customer2.id).exists()

    delete_response = client.delete(f"/api/customers/{customer2.id}/", format="json")

    assert delete_response.status_code == HTTP_204_NO_CONTENT

    assert not Customer.objects.filter(id=customer2.id).exists()

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Customer.objects.all().count()

    token_response = get_token_response(client, domain_url1, customer_user.username)
    assert token_response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_tenant_user_customer_delete(client, tenant_setup):
    """
    Tenant users cannot perform hard deletion of customers,
    every attempt will result in a soft deletion.

    Except for tenant admins and superusers, soft deleted customers will act as if they were deleted.
    There is a custom soft deletion cascade, that will cause every other object associated with that customer to be soft deleted as well.
    This also means that all users belonging to deleted customer won't be able to authenticate
    """
    tenant_user = tenant_setup["users"]["tenants"][0]
    customer_user = tenant_setup["users"]["customers"][0]
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

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Customer.objects.filter(department__organization__tenant=tenant1).count()

    assert Customer.objects.filter(id=customer1.id).exists()

    delete_response = client.delete(f"/api/customers/{customer1.local_id}/", format="json")

    assert delete_response.status_code == HTTP_204_NO_CONTENT

    assert Customer.objects.filter(id=customer1.id).exists()

    assert not Customer.objects.filter(id=customer1.id, is_deleted=False).exists()

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Customer.objects.filter(department__organization__tenant=tenant1, is_deleted=False).count()

    token_response = get_token_response(client, domain_url1, customer_user.username)
    assert token_response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_organization_user_customer_delete(client, tenant_setup):
    """
    Organization users cannot perform hard deletion of customers,
    every attempt will result in a soft deletion.

    Except for tenant admins and superusers, soft deleted customers will act as if they were deleted.
    There is a custom soft deletion cascade, that will cause every other object associated with that customer to be soft deleted as well.
    This also means that all users belonging to deleted customer won't be able to authenticate
    """

    org_user = tenant_setup["users"]["organizations"][0]
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

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Customer.objects.filter(department__organization=org_user.organization_scope, is_deleted=False).count()
    assert len(list_response.data) == Customer.objects.filter(department__organization=org_user.organization_scope).count()

    delete_response = client.delete(f"/api/customers/{customer1.local_id}/", format="json")

    assert delete_response.status_code == HTTP_204_NO_CONTENT

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Customer.objects.filter(department__organization=org_user.organization_scope, is_deleted=False).count()
    assert len(list_response.data) < Customer.objects.filter(department__organization=org_user.organization_scope).count()


@pytest.mark.django_db
def test_department_user_customer_delete(client, tenant_setup):
    """
    Department users cannot perform hard deletion of customers,
    every attempt will result in a soft deletion.

    Except for tenant admins and superusers, soft deleted customers will act as if they were deleted.
    There is a custom soft deletion cascade, that will cause every other object associated with that customer to be soft deleted as well.
    This also means that all users belonging to deleted customer won't be able to authenticate
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
    customerA = tenant_setup["customers"][departmentA][0]
    customer2 = tenant_setup["customers"][department2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, dept_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Customer.objects.filter(department=dept_user.department_scope, is_deleted=False).count()

    delete_response = client.delete(f"/api/customers/{customer1.local_id}/", format="json")

    assert delete_response.status_code == HTTP_204_NO_CONTENT

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Customer.objects.filter(department=dept_user.department_scope, is_deleted=False).count()

    delete_response = client.delete(f"/api/customers/{customer2.local_id}/", format="json")

    assert delete_response.status_code == HTTP_404_NOT_FOUND

    delete_response = client.delete(f"/api/customers/{customerA.local_id}/", format="json")

    assert delete_response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_customer_user_customer_delete(client, tenant_setup):
    """
    Customer users cannot perform hard deletion or soft deletion of customers.
    """

    customer_user = tenant_setup["users"]["customers"][0]
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

    access_token = get_access_token(client, domain_url1, customer_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 1

    delete_response = client.delete(f"/api/customers/{customer1.id}/", format="json")

    assert delete_response.status_code == HTTP_403_FORBIDDEN
