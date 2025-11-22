# Smart Meeting Room & Management System Backend

A microservices-based backend system for managing meeting room bookings, resources, availability, and reviews.

## Project Structure

```
smartmeetingroom_KatiaAbdallah_ZoraBanbouk/
├── common/                 # Shared utilities and modules
│   ├── database.py        # Database configuration
│   ├── security.py        # Security and RBAC utilities
│   ├── logging_config.py  # Logging configuration
│   ├── service_client.py  # Inter-service HTTP client
│   ├── exceptions.py      # Custom exceptions
│   └── error_handlers.py  # Global error handlers
├── services/
│   ├── users_service/     # User management service (Port 8001)
│   ├── rooms_service/     # Room management service (Port 8002)
│   ├── bookings_service/  # Booking management service (Port 8003)
│   └── reviews_service/   # Review management service (Port 8004)
├── docs/                  # Sphinx documentation
├── scripts/               # Utility scripts
├── docker-compose.yml     # Docker Compose configuration
└── requirements.txt       # Root requirements
```

## Features

- **Four Microservices**: Users, Rooms, Bookings, and Reviews
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control (RBAC)**: Admin, Regular User, Manager, Moderator, Auditor, Service Account
- **Inter-Service Communication**: Services communicate via HTTP API calls
- **Input Validation & Sanitization**: Comprehensive validation and XSS protection
- **Error Handling**: Global exception handlers for consistent error responses
- **Docker Containerization**: All services containerized with Docker
- **PostgreSQL Database**: Shared database for all services

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Running with Docker Compose

```bash
# Start all services
docker-compose up --build

# Services will be available at:
# - Users Service: http://localhost:8001
# - Rooms Service: http://localhost:8002
# - Bookings Service: http://localhost:8003
# - Reviews Service: http://localhost:8004
```

### API Documentation

Once services are running, access interactive API documentation:
- Users Service: http://localhost:8001/docs
- Rooms Service: http://localhost:8002/docs
- Bookings Service: http://localhost:8003/docs
- Reviews Service: http://localhost:8004/docs

## Development

### Setting up Local Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r services/users_service/app/requirements.txt
pip install -r services/rooms_service/app/requirements.txt
pip install -r services/bookings_service/app/requirements.txt
pip install -r services/reviews_service/requirements.txt
```

### Running Tests

```bash
# Run all tests
pytest services/*/app/tests/ -v

# Run tests for specific service
pytest services/users_service/app/tests/ -v
```

### Generating Documentation

```bash
# Install Sphinx dependencies
pip install -r docs/requirements.txt

# Generate HTML documentation
cd docs && sphinx-build -b html . _build/html

# Documentation will be available at docs/_build/html/index.html
```

### Performance Profiling

```bash
# Run profiling script
python scripts/profile_services.py

# For detailed profiling:
# CPU profiling: python -m cProfile -o profile.stats -m pytest
# Memory profiling: python -m memory_profiler your_script.py
# Coverage: pytest --cov=services --cov-report=html
```

## API Endpoints Overview

### Users Service (Port 8001)
- `POST /users` - Register new user
- `POST /token` - Login and get JWT token
- `GET /users/me` - Get current user
- `GET /users` - List all users (Admin/Auditor)
- `GET /users/{username}` - Get user by username
- `PUT /users/{username}` - Update user
- `DELETE /users/{username}` - Delete user
- `GET /users/{username}/bookings` - Get user's booking history

### Rooms Service (Port 8002)
- `POST /rooms` - Create room (Admin/Manager)
- `GET /rooms` - List/search rooms
- `GET /rooms/{room_id}` - Get room details
- `PUT /rooms/{room_id}` - Update room (Admin/Manager)
- `DELETE /rooms/{room_id}` - Delete room (Admin/Manager)
- `GET /rooms/{room_id}/availability` - Check room availability

### Bookings Service (Port 8003)
- `POST /bookings` - Create booking
- `GET /bookings` - List all bookings (Admin/Manager/Auditor)
- `GET /bookings/{booking_id}` - Get booking details
- `GET /bookings/user/{user_id}` - Get user's bookings
- `PUT /bookings/{booking_id}` - Update booking
- `POST /bookings/{booking_id}/cancel` - Cancel booking
- `GET /bookings/availability/{room_id}` - Check availability

### Reviews Service (Port 8004)
- `POST /rooms/{room_id}/reviews` - Submit review
- `GET /rooms/{room_id}/reviews` - Get room reviews
- `GET /users/{user_id}/reviews` - Get user's reviews
- `PUT /reviews/{review_id}` - Update review
- `DELETE /reviews/{review_id}` - Delete review
- `POST /reviews/{review_id}/flag` - Flag review
- `PUT /reviews/{review_id}/moderate` - Moderate review (Admin/Moderator)

## Authentication

All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

Get a token by logging in:
```bash
curl -X POST "http://localhost:8001/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"
```

## Role-Based Access Control

- **Admin**: Full system access
- **Regular User**: Manage own profile, bookings, and reviews
- **Facility Manager**: Manage rooms + view all bookings
- **Moderator**: Moderate reviews
- **Auditor**: Read-only access
- **Service Account**: Inter-service communication

## Database

The system uses PostgreSQL. Database configuration is in `docker-compose.yml`:
- Database: `smartmeeting`
- User: `smartuser`
- Password: `smartpass`
- Port: `5432`

## Testing

Test all services using Postman. Import the Postman collection from `docs/postman_collection.json`.

## Contributing

This is a project for Software Tools Lab - Fall 2025-2026.

## Authors

- Katia Abdallah
- Zora Banbouk

## License

This project is for educational purposes.

