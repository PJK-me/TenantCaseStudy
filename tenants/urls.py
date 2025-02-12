from django.urls import path
from .views import TenantCreateView

urlpatterns = [
    path('tenant/', TenantCreateView.as_view(), name='create-tenant'),
]