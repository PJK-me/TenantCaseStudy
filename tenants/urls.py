from django.urls import path
from .views import TenantCreateView, OrganizationCreateView, DepartmentCreateView, CustomerCreateView

urlpatterns = [
    path('create/tenant/', TenantCreateView.as_view(), name='create-tenant'),
    path('create/organization/', OrganizationCreateView.as_view(), name='create-organization'),
    path('create/department/', DepartmentCreateView.as_view(), name='create-department'),
    path('create/customer/', CustomerCreateView.as_view(), name='create-customer'),
]