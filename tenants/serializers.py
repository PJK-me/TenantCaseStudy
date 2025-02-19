from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from .models import Tenant, Organization, Department, Customer, Domain


class TenantSerializer(serializers.ModelSerializer):
    domain_url = serializers.CharField(write_only=True)

    class Meta:
        model = Tenant
        fields = ['id', 'name', 'domain_url']
        read_only_fields = ['id']

    def create(self, validated_data):
        domain_url = validated_data.pop('domain_url', None)
        tenant = Tenant.objects.create(**validated_data)
        if domain_url:
            Domain.objects.create(tenant=tenant, domain_url=domain_url)

        return tenant

    def update(self, instance, validated_data):
        domain_url = validated_data.pop('domain_url', None)
        instance = super().update(instance, validated_data)
        if domain_url:
            domain, created = Domain.objects.get_or_create(tenant=instance)
            domain.domain_url = domain_url
            domain.save()
        return instance


class BaseScopedSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        user = self.context['request'].user
        data = super().to_representation(instance)

        if "tenant" in data:
            data["tenant_id"] = instance.tenant.id
            data.pop("tenant", None)

        if "organization" in data:
            data["organization_id"] = instance.organization.id
            data.pop("organization", None)

        if "department" in data:
            data["department_id"] = instance.department.id
            data.pop("department", None)

        if not user.is_admin():
            data["id"] = data["local_id"]
            data.pop("local_id", None)
            data.pop("is_deleted", None)

            if "organization_id" in data:
                data["organization_id"] = instance.organization.local_id

            if "department_id" in data:
                data["department_id"] = instance.department.local_id
        else:
            if "organization_id" in data:
                data["organization_local_id"] = instance.organization.local_id

            if "department_id" in data:
                data["department_local_id"] = instance.department.local_id

        return data


class OrganizationSerializer(BaseScopedSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'local_id', 'name', 'tenant', 'is_deleted']
        read_only_fields = ['id', 'local_id', 'tenant', 'is_deleted']

    def create(self, validated_data):
        tenant = self.context.get("tenant")
        if not tenant:
            raise ValidationError("Tenant is required.")

        validated_data["tenant"] = tenant
        return super().create(validated_data)



class DepartmentSerializer(BaseScopedSerializer):
    class Meta:
        model = Department
        fields = ['id', 'local_id', 'name', 'organization', 'is_deleted']
        read_only_fields = ['id', 'local_id', 'is_deleted']

    def is_valid(self, raise_exception=False):
        user = self.context.get("request").user
        if not user.is_admin():
            organization_data = self.initial_data.get("organization")
            if isinstance(organization_data, int):
                try:
                    organization = Organization.objects.get(local_id=organization_data, tenant=user.tenant_scope)
                    self.initial_data["organization"] = organization.id
                except Organization.DoesNotExist:
                    raise NotFound("Organization with this local_id does not exist.")

        return super().is_valid(raise_exception=raise_exception)

    def create(self, validated_data):
        tenant = self.context.get("tenant")
        if not tenant:
            raise ValidationError("Tenant is required.")
        user = self.context.get("request").user
        organization = validated_data.get("organization")
        if organization and organization.tenant != tenant:
            raise PermissionDenied(f"Organization's tenant does not match the current tenant.")
        if hasattr(user, 'organization_scope') and user.organization_scope:
            if organization != user.organization_scope:
                raise PermissionDenied("You can only create departments within your assigned organization.")

        return super().create(validated_data)


class CustomerSerializer(BaseScopedSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'local_id', 'name', 'department', 'is_deleted']
        read_only_fields = ['id', 'local_id', 'is_deleted']

    def is_valid(self, raise_exception=False):
        user = self.context.get("request").user
        if not user.is_admin():
            department_data = self.initial_data.get("department")
            if isinstance(department_data, int):
                try:
                    filters = {"local_id": department_data}

                    if hasattr(user, "tenant_scope") and user.tenant_scope:
                        filters["organization__tenant"] = user.tenant_scope
                    if hasattr(user, "organization_scope") and user.organization_scope:
                        filters["organization"] = user.organization_scope

                    department = Department.objects.get(local_id=department_data, organization__tenant=user.tenant_scope)
                    if department:
                        try:
                            department = Department.objects.get(**filters)
                        except Department.DoesNotExist:
                            raise PermissionDenied("Department is outside of your scope.")
                    self.initial_data["department"] = department.id
                except Department.DoesNotExist:
                    raise NotFound("Department with this local_id does not exist.")

        return super().is_valid(raise_exception=raise_exception)

    def create(self, validated_data):
        tenant = self.context.get("tenant")
        if not tenant:
            raise ValidationError("Tenant is required.")

        department = validated_data.get("department")
        if department and department.organization.tenant != tenant:
            raise PermissionDenied("Invalid department for the current tenant.")

        user = self.context.get("request").user
        if hasattr(user, 'organization_scope') and user.organization_scope:
            if department and department.organization != user.organization_scope:
                raise PermissionDenied("You can only create customers within your assigned organization.")

        if hasattr(user, 'department_scope') and user.department_scope:
            if department and department != user.department_scope:
                raise PermissionDenied("You can only create customers within your assigned department.")

        return super().create(validated_data)

