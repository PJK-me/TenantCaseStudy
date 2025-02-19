import pytest
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN

from tenants.models import Customer
from tenants.tests.conftest import get_access_token


@pytest.mark.django_db
def test_admin_customer_list(client, tenant_setup):
    """
    Tenant admin can list of all customers, on any domain
    """
    admin_user = tenant_setup["users"]["admins"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    all_customers_count = Customer.objects.all().count()

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == all_customers_count

    client.defaults['HTTP_HOST'] = domain_url2

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == all_customers_count


@pytest.mark.django_db
def test_tenant_user_customer_list(client, tenant_setup):
    """
    Tenant user can list of all customers, on domain they are limited to.
    When trying to access customers, on a domain outside of their tenant, api returns HTTP_403_FORBIDDEN
    """
    tenant_user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Customer.objects.filter(department__organization__tenant=tenant1).count()

    client.defaults['HTTP_HOST'] = domain_url2

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_organization_user_customer_list(client, tenant_setup):
    """
    Organization user can can list of all customers that belong to their organization, but only on a domain they are limited to.
    When trying to access customers, on a domain outside of their tenant, api returns HTTP_403_FORBIDDEN
    """

    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Customer.objects.filter(department__organization=org_user.organization_scope).count()

    client.defaults['HTTP_HOST'] = domain_url2

    list_response = client.get(f"/api/customers/", format="json")
    assert list_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_department_user_customer_list(client, tenant_setup):
    """
    Organization user can can list of all customers that belong to their organization, but only on a domain they are limited to.
    When trying to access customers, on a domain outside of their tenant, api returns HTTP_403_FORBIDDEN
    """
    dept_user = tenant_setup["users"]["departments"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, dept_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == Customer.objects.filter(department=dept_user.department_scope).count()

    for element in list_response.data:
        assert element.get("department_id") == dept_user.department_scope.local_id

    client.defaults['HTTP_HOST'] = domain_url2

    list_response = client.get(f"/api/customers/", format="json")
    assert list_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_customer_user_customer_list(client, tenant_setup):
    """
    Customer user can list only a single customer - one they belong to, on domain they are limited to.
    When trying to access departments, on a domain outside of their tenant, api returns HTTP_403_FORBIDDEN
    """
    customer_user = tenant_setup["users"]["customers"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url


    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, customer_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    list_response = client.get(f"/api/customers/", format="json")

    assert list_response.status_code == HTTP_200_OK
    assert len(list_response.data) == 1

    client.defaults['HTTP_HOST'] = domain_url2

    list_response = client.get(f"/api/customers/", format="json")
    assert list_response.status_code == HTTP_403_FORBIDDEN