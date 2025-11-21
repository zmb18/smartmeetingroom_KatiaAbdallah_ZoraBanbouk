# Smart Meeting Room Backend – API Overview

## Users Service
- `POST /users` register (username, password, email, role)
- `POST /token` login (OAuth2PasswordRequestForm)
- `GET /users` list users (admin/auditor)
- `GET /users/{username}` get user (self or admin/auditor)
- `PUT /users/{username}` update user (self or admin)
- `DELETE /users/{username}` delete user (self or admin)
- `GET /users/{username}/bookings` booking history placeholder (self or admin/auditor)
- `GET /users/me` current user
- `GET /health` health check

## Rooms Service
- `POST /rooms` create room (admin/manager)
- `GET /rooms` list/search rooms (capacity/location/equipment)
- `GET /rooms/{room_id}` get room
- `PUT /rooms/{room_id}` update room (admin/manager)
- `DELETE /rooms/{room_id}` delete room (admin/manager)
- `GET /rooms/{room_id}/availability` availability/state
- `GET /health` health check

## Bookings Service
- `POST /bookings` create booking (auth; time conflict checked)
- `GET /bookings` list bookings (admin/manager/auditor)
- `GET /bookings/{booking_id}` get booking
- `PUT /bookings/{booking_id}` update booking (admin/manager)
- `POST /bookings/{booking_id}/cancel` cancel (owner or admin/manager)
- `GET /bookings/user/{user_id}` bookings by user
- `GET /bookings/availability/{room_id}` check slot availability
- `GET /health` health check

## Reviews Service
- `POST /rooms/{room_id}/reviews` create review (auth; rating 1–5; sanitized)
- `GET /rooms/{room_id}/reviews` list reviews for room
- `PUT /reviews/{review_id}` update (owner or admin/moderator)
- `DELETE /reviews/{review_id}` delete (owner or admin/moderator)
- `POST /reviews/{review_id}/flag` flag review
- `PUT /reviews/{review_id}/moderate` hide/unhide (admin/moderator)
- `GET /users/{user_id}/reviews` list reviews by user
- `GET /health` health check

## RBAC Notes
- Roles: admin, regular, manager, moderator, auditor, service.
- Enforced via JWT `role` claim; ownership checks compare JWT `sub` to resource owner where applicable.
