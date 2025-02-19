import pytest
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN

from tenants.tests.conftest import get_access_token


@pytest.mark.django_db
def test_admin_organization_get(client, tenant_setup):
    """
    Tenant admin can get an organization, on any domain, using any organization id
    """
    admin_user = tenant_setup["users"]["admins"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, admin_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response1 = client.get(f"/api/organizations/{organization1.id}/", format="json")
    assert retrieve_response1.status_code == HTTP_200_OK

    retrieved_org = retrieve_response1.data

    assert retrieved_org["id"] == organization1.id
    assert retrieved_org["name"] == organization1.name

    retrieve_response2 = client.get(f"/api/organizations/{organization2.id}/", format="json")
    assert retrieve_response2.status_code == HTTP_200_OK

    retrieved_org = retrieve_response2.data

    assert retrieved_org["id"] == organization2.id
    assert retrieved_org["name"] == organization2.name

    client.defaults['HTTP_HOST'] = domain_url2

    retrieve_response1 = client.get(f"/api/organizations/{organization1.id}/", format="json")
    assert retrieve_response1.status_code == HTTP_200_OK

    retrieved_org = retrieve_response1.data

    assert retrieved_org["id"] == organization1.id
    assert retrieved_org["name"] == organization1.name

    retrieve_response2 = client.get(f"/api/organizations/{organization2.id}/", format="json")
    assert retrieve_response2.status_code == HTTP_200_OK

    retrieved_org = retrieve_response2.data

    assert retrieved_org["id"] == organization2.id
    assert retrieved_org["name"] == organization2.name


@pytest.mark.django_db
def test_tenant_user_organization_get(client, tenant_setup):
    """
    Tenant user can get an organization, on domain that belongs to their tenant scope, using organization id
    """
    tenant_user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response1 = client.get(f"/api/organizations/{organization1.local_id}/", format="json")

    assert retrieve_response1.status_code == HTTP_200_OK

    retrieved_org = retrieve_response1.data

    assert retrieved_org["id"] == organization1.local_id
    assert retrieved_org["name"] == organization1.name


@pytest.mark.django_db
def test_tenant_user_organization_get_organization_created_on_different_domain(client, tenant_setup):
    """
    Tenant user cannot get an organization, created on domain that does not belong to their tenant scope
    Since they operate in local_id, and not actual id, its impossible for them to access other organizations
    In this case, we are using the same local_id, and get organization with that local_id inside of our scope
    """
    tenant_user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response1 = client.get(f"/api/organizations/{organization2.local_id}/", format="json")

    assert retrieve_response1.status_code == HTTP_200_OK
    assert retrieve_response1.data.get("name") != organization2.name
    assert retrieve_response1.data.get("name") == organization1.name
    assert organization2.local_id == organization1.local_id


@pytest.mark.django_db
def test_tenant_user_organization_get_mismatched_tenant(client, tenant_setup):
    """
    Tenant user cannot get an organization, created on domain that does not belong to their tenant scope,
    even if they access the api from the domain used when creating that organization.
    In other words, they are forbidden from getting an organization outside from their tenant scope
    """
    tenant_user = tenant_setup["users"]["tenants"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, tenant_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    client.defaults['HTTP_HOST'] = domain_url2

    retrieve_response1 = client.get(f"/api/organizations/{organization2.local_id}/", format="json")

    assert retrieve_response1.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_organization_user_organization_get(client, tenant_setup):
    """
    Organization user can get an organization, but only the one they are associated with.
    """
    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organizationA = tenant_setup["organizations"][tenant1][1]
    organization2 = tenant_setup["organizations"][tenant2][0]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response = client.get(f"/api/organizations/{organization1.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") == organization1.name

    retrieve_response = client.get(f"/api/organizations/{organizationA.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_404_NOT_FOUND


    retrieve_response = client.get(f"/api/organizations/{organization2.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_200_OK
    assert retrieve_response.data.get("name") == organization1.name
    assert retrieve_response.data.get("name") != organization2.name


@pytest.mark.django_db
def test_organization_user_organization_get_outside_organization_scope(client, tenant_setup):
    """
    Organization user cannot get an organization, outside of their organization scope.
    If they are permitted on specific domain, they will be limited only to organization they associated with
    """
    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]
    organization1_alter = tenant_setup["organizations"][tenant1][1]
    organization2_alter = tenant_setup["organizations"][tenant2][1]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response = client.get(f"/api/organizations/{organization1_alter.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_organization_user_organization_get_from_wrong_domain(client, tenant_setup):
    """
    Organization user cannot get an organization, from domain that does not belong to them.
    """
    org_user = tenant_setup["users"]["organizations"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]
    organization1_alter = tenant_setup["organizations"][tenant1][1]
    organization2_alter = tenant_setup["organizations"][tenant2][1]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, org_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    client.defaults['HTTP_HOST'] = domain_url2

    retrieve_response = client.get(f"/api/organizations/{organization1.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_403_FORBIDDEN

    retrieve_response = client.get(f"/api/organizations/{organization2.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_department_user_organization_get(client, tenant_setup):
    """
    Department user cannot get an organization, even if they belong to that organization.
    """
    dept_user = tenant_setup["users"]["departments"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]
    organization1_alter = tenant_setup["organizations"][tenant1][1]
    organization2_alter = tenant_setup["organizations"][tenant2][1]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, dept_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response = client.get(f"/api/organizations/{organization1.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_customer_user_organization_get(client, tenant_setup):
    """
    Customer user cannot get an organization, even if they belong to that organization.
    """
    customer_user = tenant_setup["users"]["customers"][0]
    tenant1 = tenant_setup["tenants"][0]
    tenant2 = tenant_setup["tenants"][1]
    domain_url1 = tenant_setup["domains"][tenant1].domain_url
    domain_url2 = tenant_setup["domains"][tenant2].domain_url
    organization1 = tenant_setup["organizations"][tenant1][0]
    organization2 = tenant_setup["organizations"][tenant2][0]
    organization1_alter = tenant_setup["organizations"][tenant1][1]
    organization2_alter = tenant_setup["organizations"][tenant2][1]

    client.defaults['HTTP_HOST'] = domain_url1

    access_token = get_access_token(client, domain_url1, customer_user.username)

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    retrieve_response = client.get(f"/api/organizations/{organization1.local_id}/", format="json")

    assert retrieve_response.status_code == HTTP_404_NOT_FOUND

