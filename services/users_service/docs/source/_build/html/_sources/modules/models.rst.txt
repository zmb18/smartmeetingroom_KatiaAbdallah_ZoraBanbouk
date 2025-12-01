Database Models (models.py)
===========================

.. automodule:: app.models
   :members:
   :undoc-members:
   :show-inheritance:

User Model
----------

.. autoclass:: app.models.User
   :members:
   :undoc-members:

   User account model with authentication and profile information.

   **Table Name:** users

   **Columns:**

   * ``id`` (Integer): Primary key
   * ``username`` (String(50)): Unique username, indexed
   * ``hashed_password`` (String(256)): Bcrypt hashed password
   * ``email`` (String(120)): Unique email address, indexed
   * ``full_name`` (String(120)): User's full name
   * ``role`` (String(32)): User role (admin, regular, manager, moderator, auditor, service)
   * ``is_active`` (Boolean): Account active status, defaults to True
   * ``created_at`` (DateTime): Account creation timestamp
   * ``metadata`` (JSON): Optional additional user data

Audit Log Model
---------------

.. autoclass:: app.models.AuditLog
   :members:
   :undoc-members:

   Audit log for tracking user actions.

   **Table Name:** audit_logs

   **Columns:**

   * ``id`` (Integer): Primary key
   * ``user_id`` (Integer): ID of user who performed the action
   * ``username`` (String(50)): Username of user who performed the action, indexed
   * ``action`` (String(100)): Description of the action
   * ``resource`` (String(100)): Type of resource affected
   * ``resource_id`` (String(100)): ID of the affected resource
   * ``details`` (JSON): Additional action details
   * ``created_at`` (DateTime): Timestamp of the action