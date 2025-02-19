from django.db import models


class Role(models.IntegerChoices):
    ROLE_UNNASIGNED = 0, "ROLE_UNNASIGNED"
    ROLE_TENANT_ADMIN = 1, "ROLE_TENANT_ADMIN"
    ROLE_TENANT_USER = 2, "ROLE_TENANT_USER"
    ROLE_ORG_USER = 3, "ROLE_ORG_USER"
    ROLE_DEPT_USER = 4, "ROLE_DEPT_USER"
    ROLE_CUSTOMER_USER = 5, "ROLE_CUSTOMER_USER"


class RolePermissionsManager:
    BASE_ROLE_HIERARCHY = [
        Role.ROLE_CUSTOMER_USER,
        Role.ROLE_DEPT_USER,
        Role.ROLE_ORG_USER,
        Role.ROLE_TENANT_USER,
        Role.ROLE_TENANT_ADMIN,
    ]

    BASE_ROLE_PERMISSIONS = {
        Role.ROLE_CUSTOMER_USER: {"tenants.view_customer"},
        Role.ROLE_DEPT_USER: {"tenants.view_department", "tenants.change_customer", "tenants.add_customer", "tenants.delete_customer"},
        Role.ROLE_ORG_USER: { "tenants.view_organization", "tenants.change_department", "tenants.add_department", "tenants.delete_department"},
        Role.ROLE_TENANT_USER: {"tenants.view_tenant", "tenants.change_organization", "tenants.add_organization", "tenants.delete_organization"},
        Role.ROLE_TENANT_ADMIN: {"tenants.add_tenant", "tenants.change_tenant", "tenants.delete_tenant"},
    }

    def __init__(self):
        self.ROLE_PERMISSIONS = {}
        self.ROLE_HIERARCHY = {}

        accumulated_permissions = set()
        accumulated_roles = set()
        for role in self.BASE_ROLE_HIERARCHY:
            accumulated_permissions |= self.BASE_ROLE_PERMISSIONS.get(role, set())
            self.ROLE_PERMISSIONS[role] = frozenset(accumulated_permissions)

            self.ROLE_HIERARCHY[role] = accumulated_roles
            accumulated_roles.add(role)

    def get_role_permissions(self, role):
        return self.ROLE_PERMISSIONS.get(role, set())

    def get_role_hierarchy(self, role):
        return self.ROLE_HIERARCHY.get(role, set())

    def is_role_tenant_dependant(self, role):
        return role in {
            Role.ROLE_CUSTOMER_USER,
            Role.ROLE_DEPT_USER,
            Role.ROLE_ORG_USER,
            Role.ROLE_TENANT_USER,
        }

    def is_role_organization_dependant(self, role):
        return role in {
            Role.ROLE_CUSTOMER_USER,
            Role.ROLE_DEPT_USER,
            Role.ROLE_ORG_USER,
        }

    def is_role_department_dependant(self, role):
        return role in {
            Role.ROLE_CUSTOMER_USER,
            Role.ROLE_DEPT_USER,
        }

    def is_role_customer_dependant(self, role):
        return role in {
            Role.ROLE_CUSTOMER_USER,
        }



ROLE_HIERARCHY = {
    Role.ROLE_CUSTOMER_USER: set(),
    Role.ROLE_DEPT_USER: {Role.ROLE_CUSTOMER_USER},
    Role.ROLE_ORG_USER: {Role.ROLE_DEPT_USER, Role.ROLE_CUSTOMER_USER},
    Role.ROLE_TENANT_USER: {Role.ROLE_ORG_USER, Role.ROLE_DEPT_USER, Role.ROLE_CUSTOMER_USER},
    Role.ROLE_TENANT_ADMIN: {Role.ROLE_TENANT_USER, Role.ROLE_ORG_USER, Role.ROLE_DEPT_USER, Role.ROLE_CUSTOMER_USER},
}

TENANT_ADMIN_DEPENDANT_ROLES = {

}

TENANT_DEPENDANT_ROLES = {
    Role.ROLE_CUSTOMER_USER,
    Role.ROLE_DEPT_USER,
    Role.ROLE_ORG_USER,
    Role.ROLE_TENANT_USER,
}

ORGANIZATION_DEPENDANT_ROLES = {
    Role.ROLE_CUSTOMER_USER,
    Role.ROLE_DEPT_USER,
    Role.ROLE_ORG_USER,
}

DEPARTMENT_DEPENDANT_ROLES = {
    Role.ROLE_CUSTOMER_USER,
    Role.ROLE_DEPT_USER,
}

CUSTOMER_DEPENDANT_ROLES = {
    Role.ROLE_CUSTOMER_USER,
}