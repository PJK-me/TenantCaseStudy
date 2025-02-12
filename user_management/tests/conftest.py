import os
import pytest
import django
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
django.setup()

@pytest.fixture(scope='session', autouse=True)
def setup_django():
    django.setup()


@pytest.fixture
def user(db):
    user = get_user_model().objects.create_user(username="testuser", password="password123")
    return user


@pytest.fixture
def client():
    return APIClient()