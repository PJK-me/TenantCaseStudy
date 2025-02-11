import uuid
from django.db import models, connections


class Tenant(models.Model):
    uuid = models.CharField(max_length=36, unique=True, editable=False, null=True)
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    def __str__(self):
        return self.name

class Domain(models.Model):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='domains')
    domain_url = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.domain_url