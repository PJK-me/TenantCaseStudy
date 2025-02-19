import pytest
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN

from tenants.models import Organization
from tenants.tests.conftest import get_access_token


@pytest.mark.django_db
def test_admin_organization_list(client, tenant_setup):
    """
    Tenant admin can list of all organizations, on any domain
    """
    admin_user = tenant_setup["users"]["admins"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    all_organization_count = Organization.objects.all().count()

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/organizations/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == all_organization_count

    client.defaults['HTTP_HOST'] = domain_url2

    list_response = client.get(f"/api/organizations/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == all_organization_count


@pytest.mark.django_db
def test_tenant_user_organization_list(client, tenant_setup):
    """
    Tenant user can list of all organizations, on domain they are limited to.
    When trying to access organizations, on a domain outside of their tenant, api returns HTTP_403_FORBIDDEN
    """
    tenant_user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organizations_on_tenant1 = tenant_setup["organizations"][tenant1]
    organization_on_tenant2 = tenant_setup["organizations"][tenant2]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/organizations/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Organization.objects.filter(tenant=tenant1).count()
    for element in list_response.data:
        assert element.get("tenant_id") == tenant_user.tenant_scope.id

    client.defaults['HTTP_HOST'] = domain_url2

    list_response = client.get(f"/api/organizations/", format="json")
    assert list_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_organization_user_organization_list(client, tenant_setup):
    """
    Organization user can list only a single organization - one they belong to, on domain they are limited to.
    When trying to access organizations, on a domain outside of their tenant, api returns HTTP_403_FORBIDDEN
    """
    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organizations_on_tenant1 = tenant_setup["organizations"][tenant1]
    organization_on_tenant2 = tenant_setup["organizations"][tenant2]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/organizations/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 1
    for element in list_response.data:
        assert element.get("id") == org_user.organization_scope.local_id
    assert organizations_on_tenant1[0].id == org_user.organization_scope.id

    client.defaults['HTTP_HOST'] = domain_url2

    list_response = client.get(f"/api/organizations/", format="json")
    assert list_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_department_user_organization_list(client, tenant_setup):
    """
    Department user cannot list organizations - api will return empty list
    When trying to access organizations, on a domain outside of their tenant, api returns HTTP_403_FORBIDDEN
    """
    dept_user = tenant_setup["users"]["departments"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organizations_on_tenant1 = tenant_setup["organizations"][tenant1]
    organization_on_tenant2 = tenant_setup["organizations"][tenant2]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, dept_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/organizations/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 0

    client.defaults['HTTP_HOST'] = domain_url2

    list_response = client.get(f"/api/organizations/", format="json")
    assert list_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_customer_user_organization_list(client, tenant_setup):
    """
    Customer user cannot list organizations - api will return empty list
    When trying to access organizations, on a domain outside of their tenant, api returns HTTP_403_FORBIDDEN
    """
    customer_user = tenant_setup["users"]["customers"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organizations_on_tenant1 = tenant_setup["organizations"][tenant1]
    organization_on_tenant2 = tenant_setup["organizations"][tenant2]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, customer_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/organizations/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 0

    client.defaults['HTTP_HOST'] = domain_url2

    list_response = client.get(f"/api/organizations/", format="json")
    assert list_response.status_code == HTTP_403_FORBIDDEN

