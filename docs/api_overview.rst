API Overview
=============

This document provides an overview of all API endpoints across the four services.

Users Service
-------------

Base URL: ``http://localhost:8001``

.. list-table::
   :header-rows: 1

   * - Method
     - Endpoint
     - Description
     - Auth Required
   * - POST
     - ``/users``
     - Register a new user
     - No
   * - POST
     - ``/token``
     - Login and get access token
     - No
   * - GET
     - ``/users/me``
     - Get current user info
     - Yes
   * - GET
     - ``/users``
     - List all users (Admin/Auditor only)
     - Yes
   * - GET
     - ``/users/{username}``
     - Get user by username
     - Yes
   * - PUT
     - ``/users/{username}``
     - Update user profile
     - Yes
   * - DELETE
     - ``/users/{username}``
     - Delete user account
     - Yes
   * - GET
     - ``/users/{username}/bookings``
     - Get user's booking history
     - Yes
   * - GET
     - ``/health``
     - Health check
     - No

Rooms Service
-------------

Base URL: ``http://localhost:8002``

.. list-table::
   :header-rows: 1

   * - Method
     - Endpoint
     - Description
     - Auth Required
   * - POST
     - ``/rooms``
     - Create a new room (Admin/Manager only)
     - Yes
   * - GET
     - ``/rooms``
     - List/search rooms
     - No
   * - GET
     - ``/rooms/{room_id}``
     - Get room details
     - No
   * - PUT
     - ``/rooms/{room_id}``
     - Update room (Admin/Manager only)
     - Yes
   * - DELETE
     - ``/rooms/{room_id}``
     - Delete room (Admin/Manager only)
     - Yes
   * - GET
     - ``/rooms/{room_id}/availability``
     - Check room availability
     - No
   * - GET
     - ``/health``
     - Health check
     - No

Bookings Service
----------------

Base URL: ``http://localhost:8003``

.. list-table::
   :header-rows: 1

   * - Method
     - Endpoint
     - Description
     - Auth Required
   * - POST
     - ``/bookings``
     - Create a new booking
     - Yes
   * - GET
     - ``/bookings``
     - List all bookings (Admin/Manager/Auditor only)
     - Yes
   * - GET
     - ``/bookings/{booking_id}``
     - Get booking details
     - Yes
   * - GET
     - ``/bookings/user/{user_id}``
     - Get user's bookings
     - Yes
   * - PUT
     - ``/bookings/{booking_id}``
     - Update booking
     - Yes
   * - POST
     - ``/bookings/{booking_id}/cancel``
     - Cancel a booking
     - Yes
   * - GET
     - ``/bookings/availability/{room_id}``
     - Check room availability for time slot
     - Yes
   * - GET
     - ``/health``
     - Health check
     - No

Reviews Service
---------------

Base URL: ``http://localhost:8004``

.. list-table::
   :header-rows: 1

   * - Method
     - Endpoint
     - Description
     - Auth Required
   * - POST
     - ``/rooms/{room_id}/reviews``
     - Submit a review
     - Yes
   * - GET
     - ``/rooms/{room_id}/reviews``
     - Get reviews for a room
     - No
   * - GET
     - ``/users/{user_id}/reviews``
     - Get reviews by a user
     - Yes
   * - PUT
     - ``/reviews/{review_id}``
     - Update a review
     - Yes
   * - DELETE
     - ``/reviews/{review_id}``
     - Delete a review
     - Yes
   * - POST
     - ``/reviews/{review_id}/flag``
     - Flag a review
     - Yes
   * - PUT
     - ``/reviews/{review_id}/moderate``
     - Moderate a review (Admin/Moderator only)
     - Yes
   * - GET
     - ``/health``
     - Health check
     - No

