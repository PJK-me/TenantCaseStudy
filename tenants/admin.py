from django import forms
from django.contrib import admin
from .models import Tenant, Organization, Department, Customer, Domain


class TenantAdminForm(forms.ModelForm):
    domain_url = forms.CharField(required=False, label="Domain URL", help_text="Enter the domain URL for this tenant.")

    class Meta:
        model = Tenant
        fields = ['name', 'domain_url']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            domain_instance = Domain.objects.filter(tenant=self.instance).first()
            if domain_instance:
                self.fields['domain_url'].initial = domain_instance.domain_url

class TenantAdmin(admin.ModelAdmin):
    form = TenantAdminForm
    list_display = ['id', 'name']
    readonly_fields = ['id']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        domain_url = form.cleaned_data.get('domain_url')
        if domain_url:

            domain, created = Domain.objects.get_or_create(tenant=obj, defaults={'domain_url': domain_url})
            if not created and domain.domain_url != domain_url:
                domain.domain_url = domain_url
                domain.save()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['domain_url'] = forms.CharField(required=False, label="Domain URL", help_text="Enter the domain URL for this tenant.")
        return form

class LocalIdReadOnlyAdmin(admin.ModelAdmin):
    readonly_fields = ['id', 'local_id']

admin.site.register(Tenant, TenantAdmin)
admin.site.register(Organization, LocalIdReadOnlyAdmin)
admin.site.register(Department,LocalIdReadOnlyAdmin)
admin.site.register(Customer, LocalIdReadOnlyAdmin)