from django.apps import apps
from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework.exceptions import ValidationError

from user_management.utils import (Role, ROLE_PERMISSIONS, TENANT_DEPENDANT_ROLES, ORGANIZATION_DEPENDANT_ROLES,
                                   DEPARTMENT_DEPENDANT_ROLES, CUSTOMER_DEPENDANT_ROLES, ROLE_HIERARCHY)


class BaseUser(AbstractUser):
    role = models.PositiveSmallIntegerField(choices=Role.choices, default=Role.ROLE_UNNASIGNED)
    tenant_scope = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, null=True, blank=True, db_index=True)
    organization_scope = models.ForeignKey("tenants.Organization", on_delete=models.PROTECT, null=True, blank=True, db_index=True)
    department_scope = models.ForeignKey("tenants.Department", on_delete=models.PROTECT, null=True, blank=True, db_index=True)
    customer_scope = models.ForeignKey("tenants.Customer", on_delete=models.PROTECT, null=True, blank=True, db_index=True)

    def is_admin(self):
        return self.role == Role.ROLE_TENANT_ADMIN

    def can_assign_role(self, target_user, role):
        if role not in ROLE_HIERARCHY.get(self.role, set()):
            return False

        if role in TENANT_DEPENDANT_ROLES and target_user.tenant_scope != self.tenant_scope:
            return False
        if role in ORGANIZATION_DEPENDANT_ROLES and target_user.organization_scope != self.organization_scope:
            return False
        if role in DEPARTMENT_DEPENDANT_ROLES and target_user.department_scope != self.department_scope:
            return False
        if role in CUSTOMER_DEPENDANT_ROLES and target_user.customer_scope != self.customer_scope:
            return False

        return True

    def get_limited_queryset(self, model):
        role_filters = {
            Role.ROLE_TENANT_ADMIN: {

            },
            Role.ROLE_TENANT_USER: {
                "tenant": self.tenant_scope
            },
            Role.ROLE_ORG_USER: {
                "organization": self.organization_scope,
                "organization__tenant": self.tenant_scope
            },
            Role.ROLE_DEPT_USER: {
                "department": self.department_scope,
                "department__organization": self.organization_scope,
                "department__organization__tenant": self.tenant_scope,
                "customer__department": self.department_scope
            },
            Role.ROLE_CUSTOMER_USER: {
                "id": self.customer_scope.id if self.customer_scope else None
            },

            # Role.ROLE_UNNASIGNED is not provided, so we can return model.objects.none()
        }

        filters = role_filters.get(self.role, {})

        if self.role == Role.ROLE_TENANT_ADMIN:
            return model.objects.all()
        if not filters or (self.role == Role.ROLE_CUSTOMER_USER and not self.customer_scope):
            return model.objects.none()

        queryset = model.objects.filter(**filters)
        related_fields = ["tenant", "organization", "department", "customer"]
        for field in related_fields:
            if hasattr(model, field):
                queryset = queryset.select_related(field)

        return queryset

    def has_perm(self, perm, obj=None):
        if perm not in ROLE_PERMISSIONS.get(self.role, set()):
            return False

        if self.role == Role.ROLE_UNNASIGNED:
            return False

        if not obj:
            return True

        scope_mappings = {
            "tenants.Tenant": self.tenant_scope,
            "tenants.Organization": self.organization_scope,
            "tenants.Department": self.department_scope,
            "tenants.Customer": self.customer_scope,
        }

        obj_model_name = f"{obj._meta.app_label}.{obj._meta.model_name}"
        if obj_model_name in scope_mappings and scope_mappings[obj_model_name] == obj:
            return True

        organization_model = apps.get_model('tenants', 'Organization')
        department_model = apps.get_model('tenants', 'Department')
        customer_model = apps.get_model('tenants', 'Customer')

        if isinstance(obj, organization_model) and obj.tenant == self.tenant_scope:
            return True
        if isinstance(obj, department_model) and obj.organization == self.organization_scope:
            return True
        if isinstance(obj, customer_model) and obj.department == self.department_scope:
            return True

        if self.role == Role.ROLE_ORG_USER and hasattr(obj, "organization") and obj.organization == self.organization_scope:
            return True
        if self.role == Role.ROLE_DEPT_USER and hasattr(obj, "department") and obj.department == self.department_scope:
            return True

        return False

    def clean(self):
        self._validate_tenant_scope()
        self._validate_organization_scope()
        self._validate_department_scope()
        self._validate_customer_scope()
        super().clean()

    def _validate_tenant_scope(self):
        if self.role in TENANT_DEPENDANT_ROLES and not self.tenant_scope:
            raise ValidationError({"tenant_scope": "This role requires tenant."})

    def _validate_organization_scope(self):
        if self.role in ORGANIZATION_DEPENDANT_ROLES:
            if not self.organization_scope:
                raise ValidationError({"organization_scope": "This role requires organization."})
            if self.organization_scope.tenant != self.tenant_scope:
                raise ValidationError({"organization_scope": "Organization must belong to the assigned tenant."})

    def _validate_department_scope(self):
        if self.role in DEPARTMENT_DEPENDANT_ROLES:
            if not self.department_scope:
                raise ValidationError({"department_scope": "This role requires department."})
            if self.department_scope.organization != self.organization_scope:
                raise ValidationError({"department_scope": "Department must belong to the assigned organization."})
            if self.department_scope.organization.tenant != self.tenant_scope:
                raise ValidationError(
                    {"department_scope": "Department's organization must belong to the assigned tenant."}
                )

    def _validate_customer_scope(self):
        if self.role in CUSTOMER_DEPENDANT_ROLES and not self.customer_scope:
            raise ValidationError({"customer_scope": "This role requires customer."})

    def save(self, *args, **kwargs):
        if self.pk and not self.is_superuser:
            scope_fields = ["tenant_scope", "organization_scope", "department_scope", "customer_scope"]

            old_instance = BaseUser.objects.filter(pk=self.pk).values(*scope_fields).first()

            for field in scope_fields:
                if old_instance.get(field) != getattr(self, field):
                    raise ValidationError({field: f"You cannot change your {field.replace('_', ' ')}."})

        super().save(*args, **kwargs)
