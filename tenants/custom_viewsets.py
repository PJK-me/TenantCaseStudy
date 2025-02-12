from rest_framework.viewsets import ModelViewSet

from tenants.mixins import TenantMixin


class TenantScopedModelViewSet(TenantMixin, ModelViewSet):

    def get_queryset(self):
        return super().get_queryset()

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        serializer.save(tenant=tenant)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        tenant = self.get_tenant()
        context["tenant"] = tenant
        return context