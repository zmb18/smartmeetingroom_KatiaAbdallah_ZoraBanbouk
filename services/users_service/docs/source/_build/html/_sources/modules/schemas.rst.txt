Pydantic Schemas (schemas.py)
==============================

.. automodule:: app.schemas
   :members:
   :undoc-members:
   :show-inheritance:

User Schemas
------------

Create User
~~~~~~~~~~~

.. autoclass:: app.schemas.UserCreate
   :members:
   :undoc-members:

   Schema for creating a new user account.

   **Fields:**

   * ``username``: 3-50 characters, alphanumeric and underscores only
   * ``password``: Minimum 8 characters
   * ``email``: Valid email address
   * ``full_name``: Optional, maximum 120 characters
   * ``role``: Optional, defaults to "regular"

   **Validators:**

   * ``validate_username``: Ensures only letters, digits, and underscores
   * ``validate_role``: Ensures role is in allowed list

Update User
~~~~~~~~~~~

.. autoclass:: app.schemas.UserUpdate
   :members:
   :undoc-members:

   Schema for updating user information.

   **Fields:**

   * ``email``: Optional new email
   * ``full_name``: Optional new full name
   * ``role``: Optional new role
   * ``password``: Optional new password (minimum 8 characters)

   **Validators:**

   * ``validate_role``: Ensures role is in allowed list if provided

User Output
~~~~~~~~~~~

.. autoclass:: app.schemas.UserOut
   :members:
   :undoc-members:

   Schema for user response data.

   **Fields:**

   * ``id``: User ID
   * ``username``: Username
   * ``email``: Email address
   * ``full_name``: Full name
   * ``role``: User role
   * ``is_active``: Account active status
   * ``created_at``: Creation timestamp

Authentication Schemas
----------------------

Token
~~~~~

.. autoclass:: app.schemas.Token
   :members:
   :undoc-members:

   JWT token response schema.

   **Fields:**

   * ``access_token``: JWT token string
   * ``token_type``: Token type (always "bearer")

Password Reset
~~~~~~~~~~~~~~

.. autoclass:: app.schemas.PasswordReset
   :members:
   :undoc-members:

   Password reset request schema.

   **Fields:**

   * ``new_password``: New password (minimum 8 characters)

Role Update
~~~~~~~~~~~

.. autoclass:: app.schemas.RoleUpdate
   :members:
   :undoc-members:

   Role assignment schema.

   **Fields:**

   * ``role``: New role to assign

   **Validators:**

   * ``validate_role``: Ensures role is in allowed list