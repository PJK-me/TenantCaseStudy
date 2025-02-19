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
def test_admin_organization_delete(client, tenant_setup):
    """
    Tenant admin can hard delete any department, on any domain, using any department id
    Only tenant admin or superusers are capable of true deletion.
    Deletion will cascade removing all related instances of other models.
    Any other user permitted to delete department will perform a soft deletion
    field is_deleted will be set to True, excluding it from querysets.
    Tenant admins and superusers will be able to see departments that were soft deleted.
    """
    admin_user = tenant_setup["users"]["admins"][0]
    dept_user = tenant_setup["users"]["departments"][0]
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

    list_response = client.get(f"/api/departments/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Department.objects.all().count()

    assert Department.objects.filter(id=department1.id).exists()

    delete_response = client.delete(f"/api/departments/{department1.id}/", format="json")

    assert delete_response.status_code == HTTP_204_NO_CONTENT

    assert not Department.objects.filter(id=department1.id).exists()

    list_response = client.get(f"/api/departments/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Department.objects.all().count()

    client.defaults['HTTP_HOST'] = domain_url2

    assert Department.objects.filter(id=department2.id).exists()

    delete_response = client.delete(f"/api/departments/{department2.id}/", format="json")

    assert delete_response.status_code == HTTP_204_NO_CONTENT

    assert not Department.objects.filter(id=department2.id).exists()

    list_response = client.get(f"/api/departments/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Department.objects.all().count()

    token_response = get_token_response(client, domain_url1, dept_user.username)
    assert token_response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_tenant_user_department_delete(client, tenant_setup):
    """
    Tenant users cannot perform hard deletion of departments,
    every attempt will result in a soft deletion.

    Except for tenant admins and superusers, soft deleted departments will act as if they were deleted.
    There is a custom soft deletion cascade, that will cause every other object associated with that department to be soft deleted as well.
    This also means that all users belonging to deleted department won't be able to authenticate
    """
    tenant_user = tenant_setup["users"]["tenants"][0]
    dept_user = tenant_setup["users"]["departments"][0]
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

    list_response = client.get(f"/api/departments/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Department.objects.filter(organization__tenant=tenant1).count()

    assert Department.objects.filter(id=department1.id).exists()
    assert Customer.objects.filter(department__id=department1.id, is_deleted=False).count() == Customer.objects.filter(department__id=department1.id).count()

    delete_response = client.delete(f"/api/departments/{department1.local_id}/", format="json")

    assert delete_response.status_code == HTTP_204_NO_CONTENT

    assert Department.objects.filter(id=department1.id).exists()

    assert not Department.objects.filter(id=department1.id, is_deleted=False).exists()
    assert Customer.objects.filter(department__id=department1.id, is_deleted=False).count() < Customer.objects.filter(department__id=department1.id).count()

    list_response = client.get(f"/api/departments/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Department.objects.filter(organization__tenant=tenant1, is_deleted=False).count()

    token_response = get_token_response(client, domain_url1, dept_user.username)
    assert token_response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_organization_user_department_delete(client, tenant_setup):
    """
    Organization users cannot perform hard deletion of departments,
    every attempt will result in a soft deletion.

    Except for tenant admins and superusers, soft deleted departments will act as if they were deleted.
    There is a custom soft deletion cascade, that will cause every other object associated with that department to be soft deleted as well.
    This also means that all users belonging to deleted department won't be able to authenticate
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

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/departments/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Department.objects.filter(organization=org_user.organization_scope, is_deleted=False).count()
    assert len(list_response.data) == Department.objects.filter(organization=org_user.organization_scope).count()

    delete_response = client.delete(f"/api/departments/{department1.local_id}/", format="json")

    assert delete_response.status_code == HTTP_204_NO_CONTENT

    list_response = client.get(f"/api/departments/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Department.objects.filter(organization=org_user.organization_scope, is_deleted=False).count()
    assert len(list_response.data) < Department.objects.filter(organization=org_user.organization_scope).count()

    assert Department.objects.get(id=department1.id).is_deleted

@pytest.mark.django_db
def test_department_user_department_delete(client, tenant_setup):
    """
    Department users cannot perform hard deletion or soft deletion of departments, even the one they belong to.
    """

    dept_user = tenant_setup["users"]["departments"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]
    department1 = tenant_setup["departments"][organization1][0]
    department2 = tenant_setup["departments"][organization2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, dept_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/departments/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 1

    delete_response = client.delete(f"/api/departments/{department1.local_id}/", format="json")

    assert delete_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_customer_user_department_delete(client, tenant_setup):
    """
    Customer users cannot perform hard deletion or soft deletion of departments.
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

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, customer_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/departments/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 0

    delete_response = client.delete(f"/api/departments/{department1.local_id}/", format="json")

    assert delete_response.status_code == HTTP_403_FORBIDDEN