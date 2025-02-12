from rest_framework import serializers
from .models import Tenant, Organization, Department, Customer

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name']

class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = ['id', 'name', 'tenant']
        read_only_fields = ["id", "tenant"]

    def create(self, validated_data):
        tenant = self.context.get("tenant")
        if not tenant:
            raise serializers.ValidationError({"tenant": "Tenant is required."})

        validated_data["tenant"] = tenant
        return super().create(validated_data)

class DepartmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Department
        fields = ['id', 'name', 'organization']
        read_only_fields = ["id"]

    def create(self, validated_data):
        tenant = self.context.get("tenant")
        if not tenant:
            raise serializers.ValidationError({"tenant": "Tenant is required."})

        organization = validated_data.get("organization")
        if organization and organization.tenant != tenant:
            raise serializers.ValidationError(
                {"organization": "Organization's tenant does not match the current tenant."}
            )

        return super().create(validated_data)

class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = ['id', 'name', 'department']
        read_only_fields = ["id"]

    def create(self, validated_data):
        tenant = self.context.get("tenant")
        if not tenant:
            raise serializers.ValidationError({"tenant": "Tenant is required."})

        return super().create(validated_data)