import uuid
from django.db import models, connections, connection
from django.utils import timezone


class BaseModel(models.Model):
    name = models.CharField(max_length=255, unique=True)
    local_id = models.PositiveIntegerField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def soft_delete(self):
        if self.is_deleted:
            return
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self):
        if not self.is_deleted:
            return
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])

    def get_tenant(self):
        if hasattr(self, 'tenant'):
            return self.tenant
        elif hasattr(self, 'organization'):
            return self.organization.tenant
        elif hasattr(self, 'department'):
            return self.department.organization.tenant
        return None

    def save(self, *args, **kwargs):
        if self.local_id is None:
            tenant = self.get_tenant()
            if tenant:
                schema_name = tenant.get_schema_name()
                model_name = self.__class__.__name__.lower()

                sequence_name = f"{schema_name}.{model_name}_model_local_id"

                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT nextval('{sequence_name}')")
                    self.local_id = cursor.fetchone()[0]

        super().save(*args, **kwargs)

class Tenant(BaseModel):
    uuid = models.CharField(max_length=36, unique=True, editable=False, null=True)

    def get_schema_name(self):
        return f"tenant_{self.uuid}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.uuid = str(uuid.uuid4()).replace("-", "_")
            db_schema_name = self.get_schema_name()
            with connections['default'].cursor() as cursor:
                try:

                    cursor.execute(
                        f"CREATE SCHEMA IF NOT EXISTS {db_schema_name}"
                    )

                    sequence_types = ["model", "user"]
                    sequence_names = ["organization", "department", "customer"]

                    for sequence_type in sequence_types:
                        for sequence_name in sequence_names:
                            cursor.execute(
                                f"CREATE SEQUENCE IF NOT EXISTS {db_schema_name}.{sequence_name}_{sequence_type}_local_id START WITH 1"
                            )

                    cursor.execute(
                        f"CREATE SEQUENCE IF NOT EXISTS {db_schema_name}.tenant_user_local_id START WITH 1"
                    )

                except Exception as e:
                    print(f"Error creating schema: {e}")
                    raise
        super().save(*args, **kwargs)


class Domain(models.Model):
    tenant = models.OneToOneField(Tenant, related_name='domain', on_delete=models.CASCADE)
    domain_url = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.domain_url

class Organization(BaseModel):
    tenant = models.ForeignKey(Tenant, related_name='organizations', on_delete=models.CASCADE)

class Department(BaseModel):
    organization = models.ForeignKey(Organization, related_name='departments', on_delete=models.CASCADE)

class Customer(BaseModel):
    department = models.ForeignKey(Department, related_name='customers', on_delete=models.CASCADE)