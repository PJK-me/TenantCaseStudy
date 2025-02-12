import pytest
from rest_framework import status


@pytest.mark.django_db
def test_obtain_token(client, user):
    url = "/api/token/"
    data = {
        "username": user.username,
        "password": "password123",
    }
    response = client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_protected_api_with_valid_token(client, user):
    url = "/api/token/"
    data = {
        "username": user.username,
        "password": "password123",
    }
    response = client.post(url, data, format="json")
    access_token = response.data["access"]

    protected_url = "/protected/"
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    response = client.get(protected_url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["message"] == "This is a protected view!"


@pytest.mark.django_db
def test_protected_api_with_invalid_token(client):
    protected_url = "/protected/"

    client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
    response = client.get(protected_url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_refresh_token(client, user):
    url = "/api/token/"
    data = {
        "username": user.username,
        "password": "password123",
    }
    response = client.post(url, data, format="json")
    refresh_token = response.data["refresh"]

    refresh_url = "/api/token/refresh/"
    data = {"refresh": refresh_token}
    response = client.post(refresh_url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" not in response.data
