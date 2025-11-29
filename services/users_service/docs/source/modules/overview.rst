Overview
========

The Users Service is a core component of the Smart Meeting Room System responsible for 
managing user accounts, authentication, and authorization.

Architecture
------------

The service follows a layered architecture:

* **API Layer** (main.py): FastAPI endpoints and request handling
* **Business Logic** (crud.py): CRUD operations and business rules
* **Authentication** (auth.py): JWT token management and password hashing
* **Data Layer** (models.py): SQLAlchemy ORM models
* **Validation** (schemas.py): Pydantic schemas for request/response validation
* **Configuration** (config.py): Environment-based settings

Key Components
--------------

Authentication & Security
~~~~~~~~~~~~~~~~~~~~~~~~~

* JWT token-based authentication
* Bcrypt password hashing
* OAuth2 password flow
* Role-based access control

Database
~~~~~~~~

* PostgreSQL database
* SQLAlchemy ORM
* Alembic migrations support
* User and AuditLog tables

Validation
~~~~~~~~~~

* Pydantic schemas for input validation
* Username format validation (alphanumeric + underscore)
* Email validation
* Password strength requirements (minimum 8 characters)
* Role validation against allowed values

Dependencies
------------

See ``requirements.txt`` for full list of dependencies.

Main dependencies:

* FastAPI 0.95.0
* SQLAlchemy 2.0.21
* Pydantic 1.10.11
* python-jose 3.3.0 (JWT)
* passlib 1.7.4 (password hashing)
* psycopg2-binary 2.9.6 (PostgreSQL driver)