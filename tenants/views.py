import logging

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.viewsets import ModelViewSet

from .custom_viewsets import TenantScopedModelViewSet
from .serializers import TenantSerializer, OrganizationSerializer, DepartmentSerializer, CustomerSerializer
from .decorators import tenant_scope_required
from .models import Organization, Department, Customer, Tenant


class TenantViewSet(ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated or not isinstance(user, get_user_model()):
            return super().get_queryset().none()

        model = self.queryset.model
        return user.get_limited_queryset(model)

    def create(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_admin() or user.is_superuser):
            return Response({"error": "Permission denied."}, status=403)
        return super().create(request, *args, **kwargs)


@tenant_scope_required
class OrganizationViewSet(TenantScopedModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [DjangoModelPermissions]


@tenant_scope_required
class DepartmentViewSet(TenantScopedModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [DjangoModelPermissions]


@tenant_scope_required
class CustomerViewSet(TenantScopedModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [DjangoModelPermissions]
