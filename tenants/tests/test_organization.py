import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_create_organization_with_tenant_separation(tenant_setup):
    tenant1, tenant2, domain1, domain2 = tenant_setup
    client = APIClient()

    client.defaults['HTTP_HOST'] = domain1.domain_url
    org_data = {"name": "Org A"}
    create_response = client.post("/api/organizations/", org_data, format="json")

    assert create_response.status_code == 201
    created_org = create_response.data
    org_id = created_org["id"]
    assert created_org["name"] == org_data["name"]
    assert created_org["tenant"] == tenant1.id

    list_response = client.get("/api/organizations/", format="json")
    assert list_response.status_code == 200
    assert len(list_response.data) == 1

    retrieve_response = client.get(f"/api/organizations/{org_id}/", format="json")
    assert retrieve_response.status_code == 200
    retrieved_org = retrieve_response.data
    assert retrieved_org["id"] == org_id
    assert retrieved_org["name"] == org_data["name"]

    client.defaults['HTTP_HOST'] = domain2.domain_url

    diff_domain_list_response = client.get("/api/organizations/", format="json")
    assert diff_domain_list_response.status_code == 200
    assert len(diff_domain_list_response.data) == 0

    diff_domain_retrieve_response = client.get(f"/api/organizations/{org_id}/", format="json")
    assert diff_domain_retrieve_response.status_code == 404
    retrieved_org = diff_domain_retrieve_response.data
    assert retrieved_org.get("id", None) == None
    assert retrieved_org.get("name", None) == None