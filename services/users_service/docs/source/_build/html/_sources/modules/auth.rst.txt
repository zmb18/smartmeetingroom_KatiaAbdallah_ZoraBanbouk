Authentication (auth.py)
========================

.. automodule:: app.auth
   :members:
   :undoc-members:
   :show-inheritance:

JWT Token Management
--------------------

.. autofunction:: app.auth.create_access_token

.. autofunction:: app.auth.decode_token

Password Hashing
----------------

.. autofunction:: app.auth.hash_password

.. autofunction:: app.auth.verify_password

Configuration
-------------

.. autodata:: app.auth.SECRET_KEY

.. autodata:: app.auth.ALGORITHM

.. autodata:: app.auth.ACCESS_TOKEN_EXPIRE_MINUTES

OAuth2 Scheme
-------------

.. autodata:: app.auth.oauth2_scheme

Password Context
----------------

.. autodata:: app.auth.pwd_context