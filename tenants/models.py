import uuid
from django.db import models, connections

class BaseModel(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

class Tenant(BaseModel):
    uuid = models.CharField(max_length=36, unique=True, editable=False, null=True)

    def get_schema_name(self):
        return f"tenant_{self.uuid}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.uuid = str(uuid.uuid4()).replace("-", "_")
            db_name = f"tenant_{self.uuid}"
            with connections['default'].cursor() as cursor:
                try:
                    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {db_name}")
                except Exception as e:
                    print(f"Error creating schema: {e}")
                    raise
        super().save(*args, **kwargs)



class Domain(models.Model):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='domain')
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