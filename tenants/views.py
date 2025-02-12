import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from .custom_viewsets import TenantScopedModelViewSet
from .serializers import TenantSerializer, OrganizationSerializer, DepartmentSerializer, CustomerSerializer
from .decorators import tenant_scope_required
from .models import Organization, Department, Customer


class TenantCreateView(APIView):

    def post(self, request, *args, **kwargs):
        serializer = TenantSerializer(data=request.data)
        if serializer.is_valid():
            tenant = serializer.save()
            return Response(TenantSerializer(tenant).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@tenant_scope_required
class OrganizationViewSet(TenantScopedModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        tenant = self.get_tenant()
        return Organization.objects.filter(tenant=tenant)

    def retrieve(self, request, *args, **kwargs):
        tenant = self.get_tenant()

        try:
            organization = Organization.objects.get(id=kwargs["pk"], tenant=tenant)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found for the specified organization."}, status=404)

        serializer = self.get_serializer(organization)
        return Response(serializer.data)

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        serializer.save(tenant=tenant)


@tenant_scope_required
class DepartmentViewSet(TenantScopedModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        tenant = self.get_tenant()
        return Department.objects.filter(organization__tenant=tenant)

    def retrieve(self, request, *args, **kwargs):
        tenant = self.get_tenant()
        organization_id = self.kwargs.get("organization_id")

        try:
            organization = Organization.objects.get(id=organization_id, tenant=tenant)
        except Organization.DoesNotExist:
            raise ValidationError({"organization": "Organization does not exist for this tenant."})

        try:
            department = Department.objects.get(id=kwargs["pk"], organization=organization)
        except Department.DoesNotExist:
            return Response({"error": "Department not found for the specified organization."}, status=404)

        serializer = self.get_serializer(department)
        return Response(serializer.data)

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        target_organization = serializer.validated_data.get("organization")

        if not target_organization:
            raise ValidationError({"organization": "This field is required."})

        try:
            organization = Organization.objects.get(id=target_organization.id, tenant=tenant)
        except Organization.DoesNotExist:
            raise ValidationError({"organization": "Invalid organization for the current tenant."})

        serializer.save(organization=organization)



@tenant_scope_required
class CustomerViewSet(TenantScopedModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_queryset(self):
        tenant = self.get_tenant()
        return Customer.objects.filter(department__organization__tenant=tenant)

    def retrieve(self, request, *args, **kwargs):
        tenant = self.get_tenant()
        department_id = self.kwargs.get("department_id")

        try:
            department = Department.objects.get(id=department_id, organization__tenant=tenant)
        except Department.DoesNotExist:
            raise ValidationError({"department": "Department does not exist for this tenant."})

        try:
            customer = Customer.objects.get(id=kwargs["pk"], department=department)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found for the specified department."}, status=404)

        serializer = self.get_serializer(customer)
        return Response(serializer.data)

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        target_department = serializer.validated_data.get("department")

        if not target_department:
            raise ValidationError({"department": "This field is required."})

        try:
            department = Department.objects.get(id=target_department.id, organization__tenant=tenant)
        except Department.DoesNotExist:
            raise ValidationError({"department": "Invalid department for the current tenant."})

        serializer.save(department=department)