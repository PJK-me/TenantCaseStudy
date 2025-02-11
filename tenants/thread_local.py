import threading

_tenant_storage = threading.local()


def set_tenant(tenant):
    _tenant_storage.tenant = tenant

def get_tenant():
    return getattr(_tenant_storage, 'tenant', None)

def clr_tenant():
    if hasattr(_tenant_storage, "tenant"):
        del _tenant_storage.tenant