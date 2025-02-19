from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import PermissionDenied, NotFound, AuthenticationFailed
from user_management.models import BaseUser
from tenants.models import Domain



class TenantAwareTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = BaseUser.objects.get(username=request.data.get("username"))
            domain = Domain.objects.filter(domain_url=request.get_host()).first()

            if not user.is_admin():
                if not domain:
                    raise NotFound("Domain not found.")
                if user.tenant_scope != domain.tenant:
                    raise PermissionDenied("Invalid domain for the user.")
                if user.is_deleted:
                    raise AuthenticationFailed("Authentication is unavailable. User was soft deleted.")

        return response

class TenantAwareTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            raise AuthenticationFailed({"error": "Refresh token is required."})

        try:
            decoded_token = RefreshToken(refresh_token)
            user_id = decoded_token["user_id"]
        except Exception:
            raise AuthenticationFailed({"error": "Invalid or expired refresh token."})

        try:
            user = BaseUser.objects.get(id=user_id)
        except BaseUser.DoesNotExist:
            raise NotFound({"user_not_found": "User not found."})

        domain = Domain.objects.filter(domain_url=request.get_host()).first()

        if not user.is_admin():
            if not domain:
                raise NotFound({"domain_not_found": "Domain not found."})

            if user.tenant_scope != domain.tenant:
                raise PermissionDenied({"tenant_mismatch": "Invalid domain for the user."})

            if user.is_deleted:
                raise AuthenticationFailed({"user_deleted": "Authentication is unavailable. User was soft deleted."})

        return super().post(request, *args, **kwargs)
