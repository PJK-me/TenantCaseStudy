from tenants.models import Tenant

def get_tenant_db_name(tenant_instance):
    return f"tenant_{tenant_instance.uuid}"