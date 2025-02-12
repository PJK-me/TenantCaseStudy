from rest_framework.permissions import BasePermission
from utils import Role


class UserHasTenantAdminScopeRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.status in [Role.ROLE_TENANT_ADMIN]


class UserHasTenantScopeRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.status in [Role.ROLE_TENANT_USER, Role.ROLE_TENANT_ADMIN]


class UserHasOrganizationScopeRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.status in [Role.ROLE_ORG_USER, Role.ROLE_TENANT_USER, Role.ROLE_TENANT_ADMIN]


class UserHasDepartmentScopeRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.status in [Role.ROLE_DEPT_USER, Role.ROLE_ORG_USER, Role.ROLE_TENANT_USER, Role.ROLE_TENANT_ADMIN]


class UserHasCustomerScopeRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.status in [Role.ROLE_CUSTOMER_USER, Role.ROLE_DEPT_USER, Role.ROLE_ORG_USER, Role.ROLE_TENANT_USER, Role.ROLE_TENANT_ADMIN]


class UserHasUnnasignedScopeRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.status == Role.ROLE_UNNASIGNED

class CanAssignRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if view.action == 'assign_role':
            if user.is_admin():
                return True
        return False
