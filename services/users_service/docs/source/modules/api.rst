API Endpoints (main.py)
=======================

.. automodule:: app.main
   :members:
   :undoc-members:
   :show-inheritance:

Main Application
----------------

The main FastAPI application instance with all user management endpoints.

Dependencies
~~~~~~~~~~~~

.. autofunction:: app.main.get_db

.. autofunction:: app.main.get_current_user

Endpoints
---------

User Registration & Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: app.main.register_user

.. autofunction:: app.main.login_for_token

User Profile
~~~~~~~~~~~~

.. autofunction:: app.main.read_users_me

.. autofunction:: app.main.read_user

.. autofunction:: app.main.read_users

.. autofunction:: app.main.update_user

.. autofunction:: app.main.delete_user

Admin Operations
~~~~~~~~~~~~~~~~

.. autofunction:: app.main.reset_user_password

.. autofunction:: app.main.assign_user_role

.. autofunction:: app.main.deactivate_user

.. autofunction:: app.main.activate_user

Integration
~~~~~~~~~~~

.. autofunction:: app.main.get_user_booking_history

Health Check
~~~~~~~~~~~~

.. autofunction:: app.main.health