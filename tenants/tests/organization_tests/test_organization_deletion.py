import pytest
from django.utils import timezone
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_204_NO_CONTENT, \
    HTTP_401_UNAUTHORIZED

from tenants.models import Organization, Department
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
    Tenant admin can hard delete any organization, on any domain, using any organization id
    Only tenant admin or superusers are capable of true deletion.
    Deletion will cascade removing all related instances of other models.
    Any other user permitted to delete organization will perform a soft deletion
    field is_deleted will be set to True, excluding it from querysets.
    Tenant admins and superusers will be able to see organization that were soft deleted.
    """
    admin_user = tenant_setup["users"]["admins"][0]
    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/organizations/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 4

    assert Organization.objects.filter(id=organization1.id).exists()
    assert Department.objects.filter(organization__id=organization1.id).count() == 2

    delete_response = client.delete(f"/api/organizations/{organization1.id}/", format="json")

    assert delete_response.status_code == HTTP_204_NO_CONTENT

    assert not Organization.objects.filter(id=organization1.id).exists()
    assert Department.objects.filter(organization__id=organization1.id).count() == 0

    list_response = client.get(f"/api/organizations/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 3

    client.defaults['HTTP_HOST'] = domain_url2

    assert Organization.objects.filter(id=organization2.id).exists()

    delete_response = client.delete(f"/api/organizations/{organization2.id}/", format="json")

    assert delete_response.status_code == HTTP_204_NO_CONTENT

    assert not Organization.objects.filter(id=organization2.id).exists()

    list_response = client.get(f"/api/organizations/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 2

    token_response = get_token_response(client, domain_url1, org_user.username)
    assert token_response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_tenant_user_organization_delete(client, tenant_setup):
    """
    Tenant users cannot perform hard deletion of organizations,
    every attempt will result in a soft deletion.

    Except for tenant admins and superusers, soft deleted organizations will act as if they were deleted.
    A there is a custom soft deletion cascade, that will cause every other object associated with that organization to be soft deleted as well.
    This also means that all users belonging to deleted organization won't be able to authenticate
    """
    tenant_user = tenant_setup["users"]["tenants"][0]
    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/organizations/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 2

    assert Organization.objects.filter(id=organization1.id).exists()
    assert Department.objects.filter(organization__id=organization1.id).count() == 2

    delete_response = client.delete(f"/api/organizations/{organization1.local_id}/", format="json")

    assert delete_response.status_code == HTTP_204_NO_CONTENT

    assert Organization.objects.filter(id=organization1.id).exists()
    assert Department.objects.filter(organization__id=organization1.id).count() == 2

    assert not Organization.objects.filter(id=organization1.id, is_deleted=False).exists()
    assert Department.objects.filter(organization__id=organization1.id, is_deleted=False).count() == 0

    list_response = client.get(f"/api/organizations/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 1

    token_response = get_token_response(client, domain_url1, org_user.username)
    assert token_response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_organization_user_organization_delete(client, tenant_setup):
    """
    Organization users cannot perform hard deletion or soft deletion of organizations, even the one they belong to.
    """

    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/organizations/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 1

    delete_response = client.delete(f"/api/organizations/{organization1.local_id}/", format="json")

    assert delete_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_department_user_organization_delete(client, tenant_setup):
    """
    Department users cannot perform hard deletion or soft deletion of organizations.
    """

    dept_user = tenant_setup["users"]["departments"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, dept_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/organizations/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 0

    delete_response = client.delete(f"/api/organizations/{organization1.local_id}/", format="json")

    assert delete_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_customer_user_organization_delete(client, tenant_setup):
    """
    Customer users cannot perform hard deletion or soft deletion of organizations.
    """

    customer_user = tenant_setup["users"]["customers"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, customer_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/organizations/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 0

    delete_response = client.delete(f"/api/organizations/{organization1.local_id}/", format="json")

    assert delete_response.status_code == HTTP_403_FORBIDDEN