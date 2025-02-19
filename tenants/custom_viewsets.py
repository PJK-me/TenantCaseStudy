from rest_framework import status
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from tenants.mixins import TenantMixin
from user_management.models import BaseUser
from django.views.decorators.csrf import csrf_exempt



class TenantScopedModelViewSet(TenantMixin, ModelViewSet):

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated or not isinstance(user, BaseUser):
            return super().get_queryset().none()

        model = self.queryset.model
        return user.get_limited_queryset(model)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        tenant = self.get_tenant()
        context["tenant"] = tenant
        return context

    def soft_delete_cascade(self, instance):
        soft_deleted_objects = []
        for relation in instance._meta.related_objects:
            # I'm ignoring ManyToMany relations, because they dont exist in current implementation
            if not relation.auto_created or not relation.related_model:
                continue

            accessor = relation.get_accessor_name()
            related_manager = getattr(instance, accessor, None)
            if related_manager:
                for obj in related_manager.all():
                    if hasattr(obj, "is_deleted"):
                        if not obj.is_deleted:
                            soft_deleted_objects.append(str(obj))
                            obj.soft_delete()
        return soft_deleted_objects

    def soft_delete(self, instance):
        if instance.is_deleted:
            return Response({"soft_deletion": f"{instance} is already soft deleted"},status=status.HTTP_410_GONE)

        instance.soft_delete()

        soft_deleted_objects = self.soft_delete_cascade(instance)

        return Response({"soft_deletion": f"Performed soft delete on {instance}", "soft_deletion_cascade": soft_deleted_objects}, status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        if not user.is_authenticated or not isinstance(user, BaseUser):
            raise PermissionDenied("Authentication is required for access")

        if user.is_admin() or user.is_superuser:
            return super().destroy(request, *args, **kwargs)
        else:
            instance = self.get_object()
            return self.soft_delete(instance)

    def get_object(self):
        user = self.request.user
        model = self.queryset.model
        obj_id = self.kwargs.get("pk")
        return user.get_limited_object(model, obj_id)


