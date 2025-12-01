Common Modules
==============

Shared modules used across services in the Smart Meeting Room System.

Security (common.security)
---------------------------

.. automodule:: common.security
   :members:
   :undoc-members:
   :show-inheritance:

Role Constants
~~~~~~~~~~~~~~

.. autodata:: common.security.ROLE_ADMIN
.. autodata:: common.security.ROLE_REGULAR
.. autodata:: common.security.ROLE_MANAGER
.. autodata:: common.security.ROLE_MODERATOR
.. autodata:: common.security.ROLE_AUDITOR
.. autodata:: common.security.ROLE_SERVICE

Role Functions
~~~~~~~~~~~~~~

.. autofunction:: common.security.require_role

.. autofunction:: common.security.require_any_role

Database (common.database)
---------------------------

.. automodule:: common.database
   :members:
   :undoc-members:
   :show-inheritance:

Database Functions
~~~~~~~~~~~~~~~~~~

.. autofunction:: common.database.get_engine

.. autofunction:: common.database.get_session_local

Database Objects
~~~~~~~~~~~~~~~~

.. autodata:: common.database.Base

.. autodata:: common.database.SessionLocal

.. autodata:: common.database.engine

Service Client (common.service_client)
---------------------------------------

.. automodule:: common.service_client
   :members:
   :undoc-members:
   :show-inheritance:

ServiceClient Class
~~~~~~~~~~~~~~~~~~~

.. autoclass:: common.service_client.ServiceClient
   :members:
   :undoc-members:

   HTTP client for inter-service communication.

   **Methods:**

   * ``get(endpoint, headers, params, token)``: Make GET request
   * ``post(endpoint, json_data, headers)``: Make POST request
   * ``put(endpoint, json_data, headers)``: Make PUT request
   * ``delete(endpoint, headers)``: Make DELETE request

Service Client Instances
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autodata:: common.service_client.users_client

.. autodata:: common.service_client.rooms_client

.. autodata:: common.service_client.bookings_client

.. autodata:: common.service_client.reviews_client

Error Handling (common.error_handlers)
---------------------------------------

.. automodule:: common.error_handlers
   :members:
   :undoc-members:
   :show-inheritance:

Error Handler Setup
~~~~~~~~~~~~~~~~~~~

.. autofunction:: common.error_handlers.setup_error_handlers

Exceptions (common.exceptions)
------------------------------

.. automodule:: common.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

Exception Classes
~~~~~~~~~~~~~~~~~

.. autoclass:: common.exceptions.SmartMeetingRoomException
   :members:
   :undoc-members:

.. autoclass:: common.exceptions.ValidationError
   :members:
   :undoc-members:

.. autoclass:: common.exceptions.AuthenticationError
   :members:
   :undoc-members:

.. autoclass:: common.exceptions.AuthorizationError
   :members:
   :undoc-members:

.. autoclass:: common.exceptions.ResourceNotFoundError
   :members:
   :undoc-members:

.. autoclass:: common.exceptions.ConflictError
   :members:
   :undoc-members:

.. autoclass:: common.exceptions.ServiceUnavailableError
   :members:
   :undoc-members:

Logging (common.logging_config)
--------------------------------

.. automodule:: common.logging_config
   :members:
   :undoc-members:
   :show-inheritance:

.. autofunction:: common.logging_config.setup_request_logging