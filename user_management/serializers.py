from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from .utils import Role, TENANT_DEPENDANT_ROLES


class BaseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'tenant_scope', 'organization_scope',
                  'department_scope', 'customer_scope', 'is_active', 'is_superuser']

    def validate_role(self, value):
        if value not in Role.choices:
            raise ValidationError("Invalid role assigned.")
        return value

    def validate(self, data):
        if data.get('role') in TENANT_DEPENDANT_ROLES and not data.get('tenant_scope'):
            raise ValidationError({"tenant_scope": "This role requires tenant scope."})
        return data

    def create(self, validated_data):
        user = super().create(validated_data)
        return user

    def update(self, instance, validated_data):
        if 'tenant_scope' in validated_data and not instance.is_superuser:
            raise ValidationError("You cannot change tenant scope.")
        return super().update(instance, validated_data)
