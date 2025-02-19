# Multi-Tenancy Django Application with Four Organizational Levels

## Setup
1. First clone the project & access it
	1. git clone https://github.com/PJK-me/TenantCaseStudy.git
	2. cd TenantCaseStudy
2. Create .env by coping either .env_example or .env_local
	1. cp .env_example .env <- You will need to populate fields inside the file
	2. cp .env_local .env <- This one work out of the box, no need to setup any fields
3. Run the application using Docker
	1. docker-compose up --build
4. Access the app
	1. Browsable API: http://localhost/api/
	2. Django Admin: http://localhost/admin/


## Overview
This project is a multi-tenancy Django application designed to manage 4 hierarchical organizational structures

5. Tenant - Highest level linked to Domain
6. Organization - Second highest, belonging to Tenant
7. Department - Lower unit level belonging to Organization
8. Customer - the lowest level, mostly limited to itself
