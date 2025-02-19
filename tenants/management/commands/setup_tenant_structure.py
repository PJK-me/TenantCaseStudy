from django.core.management.base import BaseCommand
from django.db import transaction
from typing import Dict, List, Any

from tenants.models import Tenant, Domain, Organization, Department, Customer
from user_management.models import BaseUser, Role


class Command(BaseCommand):
    help = "Sets up initial tenant structure and test users."

    multiplier = 2

    def handle(self, *args, **kwargs):

        if Tenant.objects.exists():
            self.stdout.write(self.style.WARNING("Tenants already exist. No objects will be created."))
        else:
            self.stdout.write(self.style.SUCCESS("Starting setup..."))
            with transaction.atomic():
                test_data = self._setup_test_data()
            self.stdout.write(self.style.SUCCESS("Tenant structure setup complete"))

    def _setup_test_data(self) :
        test_data = {
            "tenants": [],
            "domains": {},
            "organizations": {},
            "departments": {},
            "customers": {},
            "users": {
                "admins": [],
                "tenants": [],
                "organizations": [],
                "departments": [],
                "customers": [],
            },
        }

        self._create_initial_tenant()
        self._create_tenants_and_domains(test_data)
        self._create_organizations(test_data)
        self._create_departments(test_data)
        self._create_customers(test_data)
        self._create_users(test_data)

        return test_data

    def _create_initial_tenant(self):
        tenant, _ = Tenant.objects.get_or_create(name="localhost")
        Domain.objects.get_or_create(tenant=tenant, domain_url="localhost")

    def _create_tenants_and_domains(self, test_data):
        for i in range(1, self.multiplier + 1):
            tenant, _ = Tenant.objects.get_or_create(name=f"Tenant{i}")
            test_data["tenants"].append(tenant)
            domain, _ = Domain.objects.get_or_create(
                tenant=tenant, domain_url=f"tenant{i}.localhost"
            )
            test_data["domains"][tenant] = domain

    def _create_organizations(self, test_data):
        for tenant in test_data["tenants"]:
            organizations: List[Organization] = []
            for i in range(1, self.multiplier + 1):
                org_name = f"Org{i}_{tenant}"
                organization, _ = Organization.objects.get_or_create(name=org_name, tenant=tenant)
                organizations.append(organization)
            test_data["organizations"][tenant] = organizations

    def _create_departments(self, test_data):
        for tenant, organizations in test_data["organizations"].items():
            for organization in organizations:
                departments: List[Department] = []
                for i in range(1, self.multiplier + 1):
                    dept_name = f"Dept{i}_{organization}"
                    department, _ = Department.objects.get_or_create(name=dept_name, organization=organization)
                    departments.append(department)
                test_data["departments"][organization] = departments

    def _create_customers(self, test_data):
        for organization, departments in test_data["departments"].items():
            for department in departments:
                customers: List[Customer] = []
                for i in range(1, self.multiplier + 1):
                    customer_name = f"Customer{i}_{department}"
                    customer, _ = Customer.objects.get_or_create(name=customer_name, department=department)
                    customers.append(customer)
                test_data["customers"][department] = customers

    def _create_users(self, test_data):
        admin_user = BaseUser.objects.create_superuser(
            username="admin_user_1",
            password="password",
        )
        test_data["users"]["admins"].append(admin_user)

        if len(test_data["tenants"]) >= 2:
            tenant1, tenant2 = test_data["tenants"][:2]
            tenant1_user = BaseUser.objects.create_user(
                username="tenant_user_1",
                password="password",
                tenant_scope=tenant1,
            )
            tenant2_user = BaseUser.objects.create_user(
                username="tenant_user_2",
                password="password",
                tenant_scope=tenant2,
            )
            test_data["users"]["tenants"].extend([tenant1_user, tenant2_user])

            org1 = test_data["organizations"][tenant1][0]
            org2 = test_data["organizations"][tenant2][0]
            org1_user = BaseUser.objects.create_user(
                username="org_user_1",
                password="password",
                tenant_scope=tenant1,
                organization_scope=org1,
            )
            org2_user = BaseUser.objects.create_user(
                username="org_user_2",
                password="password",
                tenant_scope=tenant2,
                organization_scope=org2,
            )
            test_data["users"]["organizations"].extend([org1_user, org2_user])

            dept1 = test_data["departments"][org1][0]
            dept2 = test_data["departments"][org2][0]
            dept1_user = BaseUser.objects.create_user(
                username="dept_user_1",
                password="password",
                tenant_scope=tenant1,
                organization_scope=org1,
                department_scope=dept1,
            )
            dept2_user = BaseUser.objects.create_user(
                username="dept_user_2",
                password="password",
                tenant_scope=tenant2,
                organization_scope=org2,
                department_scope=dept2,
            )
            test_data["users"]["departments"].extend([dept1_user, dept2_user])

            customer1 = test_data["customers"][dept1][0]
            customer2 = test_data["customers"][dept2][0]
            customer1_user = BaseUser.objects.create_user(
                username="customer_user_1",
                password="password",
                tenant_scope=tenant1,
                organization_scope=org1,
                department_scope=dept1,
                customer_scope=customer1,
            )
            customer2_user = BaseUser.objects.create_user(
                username="customer_user_2",
                password="password",
                tenant_scope=tenant2,
                organization_scope=org2,
                department_scope=dept2,
                customer_scope=customer2,
            )
            test_data["users"]["customers"].extend([customer1_user, customer2_user])
