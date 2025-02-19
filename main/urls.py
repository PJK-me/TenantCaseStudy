"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tenants.views import OrganizationViewSet, DepartmentViewSet, CustomerViewSet, TenantViewSet
from user_management.views import BaseUserViewSet, ProtectedApiView
from user_management.custom_token_logic import TenantAwareTokenObtainPairView, TenantAwareTokenRefreshView

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r'users', BaseUserViewSet, basename='user')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path('protected/', ProtectedApiView.as_view(), name='protected'),
    path('api/token/', TenantAwareTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TenantAwareTokenRefreshView.as_view(), name='token_refresh'),
]
