from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework.exceptions import ValidationError

from user_management.utils import (Role, ROLE_PERMISSIONS, TENANT_DEPENDANT_ROLES, ORGANIZATION_DEPENDANT_ROLES,
                                   DEPARTMENT_DEPENDANT_ROLES, CUSTOMER_DEPENDANT_ROLES)


class BaseUser(AbstractUser):
    role = models.PositiveSmallIntegerField(choices=Role.choices, default=Role.ROLE_UNNASIGNED)
    tenant_scope = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, null=True, blank=True, db_index=True)
    organization_scope = models.ForeignKey("tenants.Organization", on_delete=models.PROTECT, null=True, blank=True, db_index=True)
    department_scope = models.ForeignKey("tenants.Department", on_delete=models.PROTECT, null=True, blank=True, db_index=True)
    customer_scope = models.ForeignKey("tenants.Customer", on_delete=models.PROTECT, null=True, blank=True, db_index=True)

    def is_admin(self):
        return self.role == Role.ROLE_TENANT_ADMIN

    def get_limited_queryset(self, model):
        role_filters = {
            Role.ROLE_TENANT_ADMIN: {
                # we are not adding any values, so it will execute models.object.filter()
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
                "department__organization__tenant": self.tenant_scope
            },
            Role.ROLE_CUSTOMER_USER: {
                "id": self.customer_scope.id
            } if self.customer_scope else {},

            # Role.ROLE_UNNASIGNED is not provided, so we can return model.objects.none()
        }

        return model.objects.filter(**role_filters.get(self.role, {})) if role_filters.get(self.role) else model.objects.none()

    def has_perm(self, perm, obj=None):
        return perm in ROLE_PERMISSIONS.get(self.role, set())

    def clean(self):
        if self.role in TENANT_DEPENDANT_ROLES and not self.tenant_scope:
            raise ValidationError(
                {"tenant_scope": f"Users with role '{self.role}' must be assigned to tenant scope."}
            )

        if self.role in ORGANIZATION_DEPENDANT_ROLES:
            if not self.organization_scope:
                raise ValidationError(
                    {"organization_scope": f"Users with role '{self.role}' must be assigned to organization scope."}
                )

            if self.organization_scope.tenant is not self.tenant_scope:
                raise ValidationError(
                    {"organization_tenant_mismatch": "User's organization scope must belong to the user's tenant scope."}
                )

        if self.role in DEPARTMENT_DEPENDANT_ROLES:
            if not self.department_scope:
                raise ValidationError(
                    {"department_scope": f"Users with role '{self.role}' must be assigned to department scope."}
                )

            if self.department_scope.organization is not self.organization_scope:
                raise ValidationError(
                    {"department_organization_mismatch": "User's department scope must belong to the user's organization scope."}
                )

        if self.role in CUSTOMER_DEPENDANT_ROLES and not self.customer_scope:
            raise ValidationError(
                {"customer_scope": f"Users with role '{self.role}' must be assigned to customer scope."}
            )
