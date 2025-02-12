from django.db import models


class Role(models.IntegerChoices):
    ROLE_UNNASIGNED = 0, "ROLE_UNNASIGNED"
    ROLE_TENANT_ADMIN = 1, "ROLE_TENANT_ADMIN"
    ROLE_TENANT_USER = 2, "ROLE_TENANT_USER"
    ROLE_ORG_USER = 3, "ROLE_ORG_USER"
    ROLE_DEPT_USER = 4, "ROLE_DEPT_USER"
    ROLE_CUSTOMER_USER = 5, "ROLE_CUSTOMER_USER"

ROLE_PERMISSIONS = {
    Role.ROLE_TENANT_ADMIN: {"view_tenant", "change_tenant", "view_organization", "change_organization", "view_department", "change_department", "view_customer", "change_customer"},
    Role.ROLE_TENANT_USER: {"view_tenant", "view_organization", "change_organization", "view_department", "change_department", "view_customer", "change_customer"},
    Role.ROLE_ORG_USER: {"view_tenant", "view_organization", "view_department", "change_department", "view_customer", "change_customer"},
    Role.ROLE_DEPT_USER: {"view_department", "view_customer", "change_customer"},
    Role.ROLE_CUSTOMER_USER: {"view_customer"},
}

ROLE_HIERARCHY = {
        Role.ROLE_TENANT_ADMIN: {Role.ROLE_TENANT_USER, Role.ROLE_ORG_USER, Role.ROLE_DEPT_USER, Role.ROLE_CUSTOMER_USER},
        Role.ROLE_TENANT_USER: {Role.ROLE_ORG_USER, Role.ROLE_DEPT_USER, Role.ROLE_CUSTOMER_USER},
        Role.ROLE_ORG_USER: {Role.ROLE_DEPT_USER, Role.ROLE_CUSTOMER_USER},
        Role.ROLE_DEPT_USER: {Role.ROLE_CUSTOMER_USER},
        Role.ROLE_CUSTOMER_USER: set(),
}

TENANT_DEPENDANT_ROLES = {
    Role.ROLE_TENANT_USER,
    Role.ROLE_ORG_USER,
    Role.ROLE_DEPT_USER,
    Role.ROLE_CUSTOMER_USER
}

ORGANIZATION_DEPENDANT_ROLES = {
    Role.ROLE_ORG_USER,
    Role.ROLE_DEPT_USER,
    Role.ROLE_CUSTOMER_USER
}

DEPARTMENT_DEPENDANT_ROLES = {
    Role.ROLE_DEPT_USER,
    Role.ROLE_CUSTOMER_USER
}

CUSTOMER_DEPENDANT_ROLES = {
    Role.ROLE_CUSTOMER_USER
}