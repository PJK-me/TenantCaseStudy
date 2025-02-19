from django.apps import apps
from django.db.models import Window, F
from django.db.models.functions import RowNumber
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, Permission, BaseUserManager
from django.db import models, connection
from rest_framework.exceptions import ValidationError, NotFound

from user_management.utils import (Role, TENANT_DEPENDANT_ROLES, ORGANIZATION_DEPENDANT_ROLES,
                                   DEPARTMENT_DEPENDANT_ROLES, CUSTOMER_DEPENDANT_ROLES, ROLE_HIERARCHY,
                                   RolePermissionsManager)

class TenantBaseUserManager(BaseUserManager):
    def create_user(self, username, password, is_admin=False, tenant_scope=None, organization_scope=None, department_scope=None, customer_scope=None,  **extra_fields):

        if is_admin:
            role = Role.ROLE_TENANT_ADMIN
        else:
            if customer_scope is not None:
                role = Role.ROLE_CUSTOMER_USER
            elif department_scope is not None:
                role = Role.ROLE_DEPT_USER
            elif organization_scope is not None:
                role = Role.ROLE_ORG_USER
            elif tenant_scope is not None:
                role = Role.ROLE_TENANT_USER
            else:
                role = Role.ROLE_UNNASIGNED

        user = self.model(
            username=username,
            role=role,
            tenant_scope=tenant_scope,
            organization_scope=organization_scope,
            department_scope=department_scope,
            customer_scope=customer_scope,
            **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, password, True, **extra_fields)

class BaseUser(AbstractUser):
    local_id = models.PositiveIntegerField(null=True, blank=True)
    role = models.PositiveSmallIntegerField(choices=Role.choices, default=Role.ROLE_UNNASIGNED)
    tenant_scope = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    organization_scope = models.ForeignKey("tenants.Organization", on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    department_scope = models.ForeignKey("tenants.Department", on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    customer_scope = models.ForeignKey("tenants.Customer", on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = TenantBaseUserManager()

    def __str__(self):
        return self.username

    def is_admin(self):
        return self.role == Role.ROLE_TENANT_ADMIN or self.is_superuser or self.is_staff

    def can_assign_role(self, target_user, role):
        role_manager = RolePermissionsManager()
        if role not in role_manager.get_role_hierarchy(self.role):
            return False

        if role_manager.is_role_tenant_dependant(self.role) and target_user.tenant_scope != self.tenant_scope:
            return False
        if role_manager.is_role_organization_dependant(self.role) and target_user.organization_scope != self.organization_scope:
            return False
        if role_manager.is_role_department_dependant(self.role) and target_user.department_scope != self.department_scope:
            return False
        if self.role is Role.ROLE_CUSTOMER_USER and target_user.customer_scope != self.customer_scope:
            return False

        return True

    def get_limited_object(self, model, obj_id):
        if self.is_admin():
            return self.get_limited_object_by_id(model, obj_id)
        return self.get_limited_object_by_local_id(model, obj_id)

    def get_limited_object_by_id(self, model, obj_id):
        try:
            return self.get_limited_queryset(model).get(id=obj_id)
        except model.DoesNotExist:
            raise NotFound(f"{model._meta.model_name} instance with id == '{obj_id}' not found in the scope of this user")

    def get_limited_object_by_local_id(self, model, obj_id):
        try:
            return self.get_limited_queryset(model).get(local_id=obj_id)
        except model.DoesNotExist:
            raise NotFound(f"{model._meta.model_name} instance with local_id == '{obj_id}' not found in the scope of this user")

    def get_limited_queryset(self, model):
        """
        Returns a queryset of objects limited to a specific model.
        Using model_role_filters, we get filters that specific role would use to get queryset
        By default Role.ROLE_TENANT_ADMIN, superusers and staff are not limited in this way
        """
        model_name = model._meta.model_name

        if self.is_admin() or self.is_superuser:
            return model.objects.all()

        # Depending on model, we change filters that each user role will use to get the queryset
        model_role_filters = {
            "tenant": {
                Role.ROLE_TENANT_USER: {
                    "id": self.tenant_scope.id if self.tenant_scope else None,
                    "is_deleted": False
                },
            },
            "organization": {
                Role.ROLE_TENANT_USER: {
                    "tenant": self.tenant_scope.id if self.tenant_scope else None,
                    "is_deleted": False
                },
                Role.ROLE_ORG_USER: {
                    "id": self.organization_scope.id if self.organization_scope else None,
                    "tenant": self.tenant_scope,
                    "is_deleted": False
                },
            },
            "department": {
                Role.ROLE_TENANT_USER: {
                    "organization__tenant": self.tenant_scope.id if self.tenant_scope else None,
                    "is_deleted": False
                },
                Role.ROLE_ORG_USER: {
                    "organization": self.organization_scope.id if self.organization_scope else None,
                    "organization__tenant": self.tenant_scope,
                    "is_deleted": False
                },
                Role.ROLE_DEPT_USER: {
                    "id": self.department_scope.id if self.department_scope else None,
                    "organization": self.organization_scope,
                    "organization__tenant": self.tenant_scope,
                    "is_deleted": False
                },
            },
            "customer": {
                Role.ROLE_TENANT_USER: {
                    "department__organization__tenant": self.tenant_scope.id if self.tenant_scope else None,
                    "is_deleted": False
                },
                Role.ROLE_ORG_USER: {
                    "department__organization": self.organization_scope.id if self.organization_scope else None,
                    "department__organization__tenant": self.tenant_scope,
                    "is_deleted": False
                },
                Role.ROLE_DEPT_USER: {
                    "department": self.department_scope.id if self.department_scope else None,
                    "department__organization": self.organization_scope,
                    "department__organization__tenant": self.tenant_scope,
                    "is_deleted": False
                },
                Role.ROLE_CUSTOMER_USER: {
                    "id": self.customer_scope.id if self.customer_scope else None,
                    "department": self.department_scope,
                    "department__organization": self.organization_scope,
                    "department__organization__tenant": self.tenant_scope,
                    "is_deleted": False
                },
            },
            "baseuser": {
                Role.ROLE_TENANT_USER: {
                    "tenant_scope": self.tenant_scope,
                    "is_deleted": False
                },
                Role.ROLE_ORG_USER: {
                    "organization_scope": self.organization_scope,
                    "tenant_scope": self.tenant_scope,
                    "is_deleted": False
                },
                Role.ROLE_DEPT_USER: {
                    "department_scope": self.department_scope,
                    "organization_scope": self.organization_scope,
                    "tenant_scope": self.tenant_scope,
                    "is_deleted": False
                },
                Role.ROLE_CUSTOMER_USER: {
                    "customer_scope": self.customer_scope,
                    "department_scope": self.department_scope,
                    "organization_scope": self.organization_scope,
                    "tenant_scope": self.tenant_scope,
                    "is_deleted": False
                },
            },

        }

        filters = model_role_filters.get(model_name, {}).get(self.role, {})

        # if filters are empty - then it means that Role does not allow to access any instances of that model
        if not filters or (self.role == Role.ROLE_CUSTOMER_USER and not self.customer_scope):
            return model.objects.none()

        queryset = model.objects.filter(**filters)
        related_fields = ["tenant", "organization", "department", "customer"]
        for field in related_fields:
            if hasattr(model, field):
                queryset = queryset.select_related(field)

        return queryset

    def has_perm(self, perm, obj=None):
        role_manager = RolePermissionsManager()

        if perm not in role_manager.get_role_permissions(self.role):
            return False

        if self.role == Role.ROLE_UNNASIGNED:
            return False

        # if we are not checking obj permissions, then we can return True
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

    def _assign_permission(self, permission):
        app_label, perm_codename = permission.split(".")
        permission = Permission.objects.filter(codename=perm_codename, content_type__app_label=app_label).first()
        if permission and permission not in self.user_permissions.all():
            self.user_permissions.add(permission)

    def _assign_role_permissions(self, role_manager):
        if self.role is not None:
            for permission in role_manager.get_role_permissions(self.role):
                self._assign_permission(permission)

    def _reset_role_permissions(self, role_manager):
        self.user_permissions.clear()
        self._assign_role_permissions(role_manager)

    def soft_delete(self):
        if self.is_deleted:
            return
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(skip_scope_validation=True, update_fields=["is_deleted", "deleted_at"])

    def restore(self):
        if self.is_deleted:
            return
        self.is_deleted = False
        self.deleted_at = None
        self.save(skip_scope_validation=True, update_fields=["is_deleted", "deleted_at"])

    def get_lowest_scope(self):
        if self.customer_scope:
            return "customer"
        if self.department_scope:
            return "department"
        if self.organization_scope:
            return "organization"
        if self.tenant_scope:
            return "tenant"
        return None

    def save(self, *args, skip_scope_validation=False, **kwargs):
        initial_setup = self.pk is None
        role_manager = RolePermissionsManager()

        if self.local_id is None and not self.is_admin():
            tenant = self.tenant_scope
            if tenant:
                schema_name = tenant.get_schema_name()
                model_name = self.get_lowest_scope()

                sequence_name = f"{schema_name}.{model_name}_user_local_id"

                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT nextval('{sequence_name}')")
                    self.local_id = cursor.fetchone()[0]

        if self.pk and not skip_scope_validation:

            if not self.is_admin() or not self.is_superuser:
                scope_fields = ["tenant_scope", "organization_scope", "department_scope", "customer_scope", "role"]

                old_instance = BaseUser.objects.get(pk=self.pk)

                for field in scope_fields:
                    if getattr(old_instance, field) != getattr(self, field):
                        raise ValidationError(
                            {
                                field: f"You cannot change your {field.replace('_', ' ')}.",
                             }
                        )

                if old_instance.role != self.role:
                    self._reset_role_permissions(role_manager)

        super().save(*args, **kwargs)

        if initial_setup:
            # assigning roles, happens after creating id (necessary for many to many fields)
            self._assign_role_permissions(role_manager)




