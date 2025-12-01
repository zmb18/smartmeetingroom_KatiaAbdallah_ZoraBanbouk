Configuration (config.py)
=========================

.. automodule:: app.config
   :members:
   :undoc-members:
   :show-inheritance:

Settings Class
--------------

.. autoclass:: app.config.Settings
   :members:
   :undoc-members:

   Application configuration settings loaded from environment variables.

   **Database Configuration:**

   * ``SQLALCHEMY_DATABASE_URL``: PostgreSQL connection string
     
     Default: ``postgresql://postgres:password@db:5432/users_db``

   **JWT Configuration:**

   * ``SECRET_KEY``: Secret key for JWT signing
     
     Default: ``your-secret-key-change-in-production``
     
     **⚠️ Must be changed in production!**

   * ``ALGORITHM``: JWT encoding algorithm
     
     Value: ``HS256``

   * ``ACCESS_TOKEN_EXPIRE_MINUTES``: Token expiration time
     
     Default: ``30`` minutes

   **Service Configuration:**

   * ``SERVICE_NAME``: Name of the service
     
     Value: ``Users Service``

   * ``DEBUG``: Debug mode flag
     
     Default: ``False``

   **API Configuration:**

   * ``API_PREFIX``: API route prefix
     
     Value: ``/api/v1``

Settings Instance
-----------------

.. autodata:: app.config.settings

   Global settings instance used throughout the application.

Environment Variables
---------------------

The following environment variables can be set to configure the service:

* ``DATABASE_URL``: Override default database connection
* ``SECRET_KEY``: Set JWT secret key (required for production)
* ``DEBUG``: Enable debug mode (set to "true")

Example ``.env`` file::

    DATABASE_URL=postgresql://user:pass@localhost:5432/users_db
    SECRET_KEY=your-super-secret-key-here
    DEBUG=false