import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_create_department_with_tenant_separation(tenant_setup):
    tenant1, tenant2, domain1, domain2 = tenant_setup
    client = APIClient()

    client.defaults['HTTP_HOST'] = domain1.domain_url
    org_data = {"name": "Org A"}
    org_response = client.post("/api/create/organization/", org_data, format="json")
    assert org_response.status_code == 201
    org_id = org_response.data["id"]

    department_data = {"name": "Department A", "organization": org_id}
    response = client.post("/api/create/department/", department_data, format="json")

    assert response.status_code == 201
    assert response.data["name"] == "Department A"
    assert response.data["organization"] == org_id