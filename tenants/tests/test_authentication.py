import pytest
from rest_framework import status

@pytest.mark.django_db
def test_admin_authentication(client, tenant_setup):
     url = "/api/token/"

     tenant1 = tenant_setup["tenants"][0]
     tenant2 = tenant_setup["tenants"][1]
     domain_url1 = tenant_setup["domains"][tenant1].domain_url
     domain_url2 = tenant_setup["domains"][tenant2].domain_url

     data = {
          "username": tenant_setup["users"]["admins"][0].username,
          "password": "password",
     }

     client.defaults['HTTP_HOST'] = "tenant1.localhost" # domain_url1

     response = client.post(url, data, format="json")

     assert response.status_code == status.HTTP_200_OK
     assert "access" in response.data
     assert "refresh" in response.data

     client.defaults['HTTP_HOST'] = domain_url2

     response = client.post(url, data, format="json")

     assert response.status_code == status.HTTP_200_OK
     assert "access" in response.data
     assert "refresh" in response.data


@pytest.mark.django_db
def test_tenant_user_authentication(client, tenant_setup):
     url = "/api/token/"

     tenant1 = tenant_setup["tenants"][0]
     tenant2 = tenant_setup["tenants"][1]
     domain_url1 = tenant_setup["domains"][tenant1].domain_url
     domain_url2 = tenant_setup["domains"][tenant2].domain_url

     data = {
          "username": tenant_setup["users"]["tenants"][0].username,
          "password": "password",
     }

     client.defaults['HTTP_HOST'] = domain_url1

     response = client.post(url, data, format="json")

     assert response.status_code == status.HTTP_200_OK
     assert "access" in response.data
     assert "refresh" in response.data

     client.defaults['HTTP_HOST'] = domain_url2

     response = client.post(url, data, format="json")

     assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_organization_user_authentication(client, tenant_setup):
     url = "/api/token/"

     tenant1 = tenant_setup["tenants"][0]
     tenant2 = tenant_setup["tenants"][1]
     domain_url1 = tenant_setup["domains"][tenant1].domain_url
     domain_url2 = tenant_setup["domains"][tenant2].domain_url

     data = {
          "username": tenant_setup["users"]["organizations"][0].username,
          "password": "password",
     }

     client.defaults['HTTP_HOST'] = domain_url1

     response = client.post(url, data, format="json")

     assert response.status_code == status.HTTP_200_OK
     assert "access" in response.data
     assert "refresh" in response.data

     client.defaults['HTTP_HOST'] = domain_url2

     response = client.post(url, data, format="json")

     assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_department_user_authentication(client, tenant_setup):
     url = "/api/token/"

     tenant1 = tenant_setup["tenants"][0]
     tenant2 = tenant_setup["tenants"][1]
     domain_url1 = tenant_setup["domains"][tenant1].domain_url
     domain_url2 = tenant_setup["domains"][tenant2].domain_url

     data = {
          "username": tenant_setup["users"]["departments"][0].username,
          "password": "password",
     }

     client.defaults['HTTP_HOST'] = domain_url1

     response = client.post(url, data, format="json")

     assert response.status_code == status.HTTP_200_OK
     assert "access" in response.data
     assert "refresh" in response.data

     client.defaults['HTTP_HOST'] = domain_url2

     response = client.post(url, data, format="json")

     assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_customer_user_authentication(client, tenant_setup):
     url = "/api/token/"

     tenant1 = tenant_setup["tenants"][0]
     tenant2 = tenant_setup["tenants"][1]
     domain_url1 = tenant_setup["domains"][tenant1].domain_url
     domain_url2 = tenant_setup["domains"][tenant2].domain_url

     data = {
          "username": tenant_setup["users"]["customers"][0].username,
          "password": "password",
     }

     client.defaults['HTTP_HOST'] = domain_url1

     response = client.post(url, data, format="json")

     assert response.status_code == status.HTTP_200_OK
     assert "access" in response.data
     assert "refresh" in response.data

     client.defaults['HTTP_HOST'] = domain_url2

     response = client.post(url, data, format="json")

     assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_incorrect_user_authentication(client, tenant_setup):
     url = "/api/token/"

     tenant1 = tenant_setup["tenants"][0]
     tenant2 = tenant_setup["tenants"][1]
     domain_url1 = tenant_setup["domains"][tenant1].domain_url
     domain_url2 = tenant_setup["domains"][tenant2].domain_url

     data = {
          "username": "wrong_user",
          "password": "password",
     }

     client.defaults['HTTP_HOST'] = domain_url1

     response = client.post(url, data, format="json")

     assert response.status_code == status.HTTP_401_UNAUTHORIZED

     client.defaults['HTTP_HOST'] = domain_url2

     response = client.post(url, data, format="json")

     assert response.status_code == status.HTTP_401_UNAUTHORIZED
