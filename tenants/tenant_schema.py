from asgiref.local import Local
from django.db.backends.signals import connection_created


_thread_locals = Local()

def set_tenant_schema(tenant_schema_name):
    _thread_locals.schema_name = tenant_schema_name

def get_tenant_schema():
    return getattr(_thread_locals, 'schema_name', None)

def apply_schema(connection, sender, **kwargs):
    schema_name = get_tenant_schema()
    if schema_name:
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {schema_name}, public;')

# Connecting the signal
connection_created.connect(apply_schema)