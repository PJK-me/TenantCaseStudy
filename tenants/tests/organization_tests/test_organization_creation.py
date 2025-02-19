import pytest
from rest_framework import status
from tenants.models import Organization
from tenants.tests.conftest import get_access_token


@pytest.mark.django_db
def test_admin_organization_create(client, tenant_setup):
    """
    Tenant admin can create an organization, on any domain
    """
    admin_user = tenant_setup["users"]["admins"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url = tenant_setup["domains"][tenant1].domain_url

    client.defaults['HTTP_HOST'] = domain_url

    access_token = get_access_token(client, domain_url, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    org_data = {"name": "Org A"}
    org_response = client.post("/api/organizations/", org_data, format="json")

    assert org_response.status_code == status.HTTP_201_CREATED
    assert org_response.json()["name"] == "Org A"

    org_id = org_response.json()["id"]

    created_org = Organization.objects.get(id=org_id)
    assert created_org.tenant == tenant_setup["domains"][tenant1].tenant
    assert created_org.tenant != tenant_setup["domains"][tenant2].tenant


@pytest.mark.django_db
def test_tenant_user_organization_create(client, tenant_setup):
    """
    Tenant user can create an organization, on domain inside their scope
    Its important to note that the id returned by api, is actually local_api
    """
    tenant_user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    assert tenant_user.tenant_scope == tenant1

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    org_data = {"name": "Org A"}
    org_response = client.post("/api/organizations/", org_data, format="json")

    assert org_response.status_code == status.HTTP_201_CREATED
    assert org_response.json()["name"] == "Org A"

    org_id = org_response.json()["id"]

    created_org = Organization.objects.get(local_id=org_id, tenant=tenant_user.tenant_scope)
    assert created_org.tenant == tenant_user.tenant_scope


@pytest.mark.django_db
def test_tenant_user_organization_create_with_mismatched_tenant(client, tenant_setup):
    """
    Tenant users cannot create new organizations, on domains outside their tenant scope.
    """
    tenant_user = tenant_setup["users"]["tenants"][1]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    client.defaults['HTTP_HOST'] = domain_url2

    access_token = get_access_token(client, domain_url2, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    # switching to domain, that the user should not be able to govern
    client.defaults['HTTP_HOST'] = domain_url1

    org_data = {"name": "Org A"}
    org_response = client.post("/api/organizations/", org_data, format="json")

    assert org_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_organization_user_organization_create(client, tenant_setup):
    """
    Organization users cannot create new organizations.
    """
    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    org_data = {"name": "Org A"}
    org_response = client.post("/api/organizations/", org_data, format="json")

    assert org_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_department_user_organization_create(client, tenant_setup):
    """
    Department users cannot create new organizations.
    """
    dept_user = tenant_setup["users"]["departments"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, dept_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    org_data = {"name": "Org A"}
    org_response = client.post("/api/organizations/", org_data, format="json")

    assert org_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_customer_user_organization_create(client, tenant_setup):
    """
    Customer users cannot create new organizations.
    """
    customer_user = tenant_setup["users"]["customers"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, customer_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    org_data = {"name": "Org A"}
    org_response = client.post("/api/organizations/", org_data, format="json")

    assert org_response.status_code == status.HTTP_403_FORBIDDEN
