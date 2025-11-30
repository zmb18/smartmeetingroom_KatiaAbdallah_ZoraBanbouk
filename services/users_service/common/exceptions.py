"""
Custom exception classes for the Smart Meeting Room system
"""
from fastapi import HTTPException, status


class SmartMeetingRoomException(HTTPException):
    """Base exception for Smart Meeting Room system"""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class ValidationError(SmartMeetingRoomException):
    """Raised when input validation fails"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class AuthenticationError(SmartMeetingRoomException):
    """Raised when authentication fails"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthorizationError(SmartMeetingRoomException):
    """Raised when authorization fails"""
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ResourceNotFoundError(SmartMeetingRoomException):
    """Raised when a requested resource is not found"""
    def __init__(self, resource_type: str = "Resource", resource_id: str = None):
        detail = f"{resource_type} not found"
        if resource_id:
            detail += f": {resource_id}"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(SmartMeetingRoomException):
    """Raised when there's a conflict (e.g., duplicate, booking conflict)"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ServiceUnavailableError(SmartMeetingRoomException):
    """Raised when an external service is unavailable"""
    def __init__(self, service_name: str = "Service", detail: str = None):
        detail_msg = f"{service_name} is unavailable"
        if detail:
            detail_msg += f": {detail}"
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail_msg)

