from asgiref.local import Local
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import ValidationError, PermissionDenied, APIException, AuthenticationFailed
from rest_framework.renderers import JSONRenderer
from tenants.models import Tenant
from exception_handlers import custom_exception_handler
from .tenant_schema import set_tenant_schema


_thread_locals = Local()


def get_current_tenant():
    return getattr(_thread_locals, 'tenant', None)


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            domain_tenant = self.get_tenant_from_request(request)
            tenant = None

            if (
                    request.path == "/api/"
                    or request.path.startswith("/admin/")
                    or request.path.startswith("/api-auth/")
                    or request.path.startswith("/api/token/")
            ):
                # api root, /admin/, /api/token/ and /api-auth/ are exempt
                # this makes it easier to use browsable api, and to switch users
                return self.get_response(request)

            if isinstance(request.user, AnonymousUser):
                request.user = self.get_user_from_token(request)

            if not hasattr(request.user, "tenant_scope") or getattr(request.user, "tenant_scope", None) is None:
                # admin users and unauthenticated users use domain_tenant
                # unauthenticated users, will not be able to access any other api endpoint (401)
                tenant = domain_tenant
            else:
                if not domain_tenant:
                    raise ValidationError("No tenant")
                tenant_scope = getattr(request.user, "tenant_scope")
                if tenant_scope != domain_tenant:
                    raise PermissionDenied(f"user belongs to a different tenant. User tenant is {tenant_scope} while domain tenant is {domain_tenant}")
                else:
                    tenant = tenant_scope

            if not tenant:
                raise PermissionDenied(f"Domain '{request.get_host()} 'does not exist in the system. Create new tenant with this domain_url, to access the app through it")

            set_tenant_schema(tenant.get_schema_name())
            _thread_locals.tenant = tenant
            request.tenant = tenant

            response = self.get_response(request)

            return response
        except APIException as e:
            return self._handle_exception(e, request)

    def _handle_exception(self, exc, request):
        response = custom_exception_handler(exc, {'request': request})

        if response is None:
            from rest_framework.response import Response
            response = Response({"detail": "An unexpected error occurred."}, status=500)

        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = "application/json"
        response.renderer_context = {'request': request}
        response.render()
        return response

    def get_tenant_from_request(self, request):
        domain = request.get_host()

        try:
            tenant = Tenant.objects.get(domain__domain_url=domain)
            set_tenant_schema(tenant.get_schema_name())
            return tenant
        except Tenant.DoesNotExist:
            return None

    def get_user_from_token(self, request):
        try:
            user_auth_tuple = JWTAuthentication().authenticate(request)
            if user_auth_tuple:
                return user_auth_tuple[0]
        except AuthenticationFailed:
            pass

        return None



