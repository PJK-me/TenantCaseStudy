from django.contrib import admin

from .models import Tenant, Organization, Department, Customer

admin.site.register(Tenant)
admin.site.register(Organization)
admin.site.register(Department)
admin.site.register(Customer)