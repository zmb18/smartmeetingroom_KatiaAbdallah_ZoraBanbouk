Smart Meeting Room & Management System Backend Documentation
=============================================================

Welcome to the Smart Meeting Room & Management System Backend API documentation.

This system consists of four microservices that manage various aspects of meeting room bookings, resources, room availability, and review management.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api_overview
   users_service
   rooms_service
   bookings_service
   reviews_service
   authentication
   rbac

Overview
--------

The Smart Meeting Room & Management System Backend is a microservices-based architecture designed to handle:

* **User Management**: User accounts, authentication, and authorization
* **Room Management**: Meeting room details, availability, and equipment
* **Booking Management**: Room reservations, availability checks, and booking history
* **Review Management**: Room reviews, ratings, and moderation

Architecture
-----------

The system consists of four independent services:

1. **Users Service** (Port 8001): Manages user accounts and authentication
2. **Rooms Service** (Port 8002): Manages meeting rooms and their details
3. **Bookings Service** (Port 8003): Manages room bookings and availability
4. **Reviews Service** (Port 8004): Manages room reviews and ratings

All services communicate via HTTP API calls and share a common PostgreSQL database.

Authentication
--------------

The system uses JWT (JSON Web Tokens) for authentication. Users authenticate via the Users Service and receive a token that is used for subsequent API calls to all services.

Role-Based Access Control (RBAC)
----------------------------------

The system implements the following roles:

* **Admin**: Full system access
* **Regular User**: Can manage own profile, bookings, and reviews
* **Facility Manager**: Can manage rooms and view all bookings
* **Moderator**: Can moderate reviews
* **Auditor**: Read-only access to all resources
* **Service Account**: For inter-service communication

For detailed information about each service, see the service-specific documentation sections.

