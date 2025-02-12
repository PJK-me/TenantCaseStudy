import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Tenant, Organization, Department, Customer
from .serializers import TenantSerializer, OrganizationSerializer, DepartmentSerializer, CustomerSerializer
from .decorators import tenant_scope_required

class TenantCreateView(APIView):

    def post(self, request, *args, **kwargs):
        serializer = TenantSerializer(data=request.data)
        if serializer.is_valid():
            tenant = serializer.save()
            return Response(TenantSerializer(tenant).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@tenant_scope_required
class OrganizationCreateView(APIView):

    def post(self, request, *args, **kwargs):
        tenant = kwargs.get("tenant")

        if not tenant:
            return Response({"error": "Tenant not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrganizationSerializer(data=request.data, context={"tenant": tenant})

        if serializer.is_valid():
            organization = serializer.save(tenant=tenant)
            return Response(OrganizationSerializer(organization).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@tenant_scope_required
class DepartmentCreateView(APIView):

    def post(self, request, *args, **kwargs):
        tenant = kwargs.get("tenant")

        if not tenant:
            return Response({"error": "Tenant not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = DepartmentSerializer(data=request.data, context={"tenant": tenant})
        if serializer.is_valid():
            department = serializer.save()
            return Response(DepartmentSerializer(department).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@tenant_scope_required
class CustomerCreateView(APIView):

    def post(self, request, *args, **kwargs):
        tenant = kwargs.get("tenant")

        if not tenant:
            return Response({"error": "Tenant not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CustomerSerializer(data=request.data, context={"tenant": tenant})
        if serializer.is_valid():
            customer = serializer.save()
            return Response(CustomerSerializer(customer).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)