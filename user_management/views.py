from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import BaseUserSerializer
from user_management.utils import Role

class ProtectedApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "This is a protected view!"})

class BaseUserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = BaseUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user

        if user.is_admin():
            return get_user_model().objects.all()
        else:
            return user.get_limited_queryset(get_user_model())

    def create(self, request, *args, **kwargs):
        if request.user.role not in [Role.ROLE_TENANT_ADMIN]:
            raise PermissionDenied("You don't have permission to create users.")

        return super().create(request, *args, **kwargs)

    def perform_update(self, serializer):
        user = serializer.instance
        if user.is_superuser:
            super().perform_update(serializer)
        else:
            restricted_fields = ["tenant_scope", "organization_scope", "department_scope", "customer_scope"]
            for field in restricted_fields:
                if field in serializer.validated_data:
                    raise ValidationError(f"You cannot change {field.replace('_', ' ')} for this user.")
            super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.is_admin():
            raise PermissionDenied("You don't have permission to delete this user.")
        super().perform_destroy(instance)
