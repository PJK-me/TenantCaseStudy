from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from .utils import Role, TENANT_DEPENDANT_ROLES


class BaseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'local_id', 'username', 'role', 'tenant_scope', 'organization_scope',
                  'department_scope', 'customer_scope', 'is_deleted', 'is_superuser']
        read_only_fields = ['id', 'local_id', 'role', 'is_deleted']

    def validate_role(self, value):
        if value not in Role.choices:
            raise ValidationError("Invalid role assigned.")
        return value

    def validate(self, data):
        if data.get('role') in TENANT_DEPENDANT_ROLES and not data.get('tenant_scope'):
            raise ValidationError("This role requires tenant scope.")
        return data

    def create(self, validated_data):
        user = super().create(validated_data)
        return user

    def update(self, instance, validated_data):
        if 'tenant_scope' in validated_data and not instance.is_superuser:
            raise ValidationError("You cannot change tenant scope.")
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        user = self.context['request'].user
        data = super().to_representation(instance)

        if not user.is_admin():
            data["id"] = data["local_id"]
            data.pop("local_id", None)
            data.pop("is_deleted", None)

            if "organization_scope" in data:
                if getattr(instance, "organization_scope", None) is not None:
                    data["organization_scope"] = instance.organization_scope.local_id
                else:
                    data.pop("organization_scope", None)

            if "department_scope" in data:
                if getattr(instance, "department_scope", None) is not None:
                    data["department_scope"] = instance.department_scope.local_id
                else:
                    data.pop("department_scope", None)

            if "customer_scope" in data:
                if getattr(instance, "customer_scope", None) is not None:
                    data["customer_scope"] = instance.organization_scope.local_id
                else:
                    data.pop("customer_scope", None)

        return data


