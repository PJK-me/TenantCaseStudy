from .middleware import get_current_tenant

class TenantDatabaseRouter:
    def db_for_read(self, model, **hints):
        tenant = get_current_tenant()
        if tenant:
            return tenant.db_alias
        return None

    def db_for_write(self, model, **hints):
        tenant = get_current_tenant()
        if tenant:
            return tenant.db_alias
        return None