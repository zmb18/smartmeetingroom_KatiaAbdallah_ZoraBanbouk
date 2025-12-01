"""
Service client for inter-service HTTP communication
"""
import os
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

# Service URLs - can be overridden via environment variables
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://users_service:8001")
ROOMS_SERVICE_URL = os.getenv("ROOMS_SERVICE_URL", "http://rooms_service:8002")
BOOKINGS_SERVICE_URL = os.getenv("BOOKINGS_SERVICE_URL", "http://bookings_service:8003")
REVIEWS_SERVICE_URL = os.getenv("REVIEWS_SERVICE_URL", "http://reviews_service:8004")

class ServiceClient:
    """HTTP client for calling other services"""
    
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url
        self.timeout = timeout
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to service"""
        url = f"{self.base_url}{endpoint}"
        request_headers = headers or {}
        
        # Add token if provided (but don't override if already in headers)
        if token and "Authorization" not in request_headers:
            request_headers["Authorization"] = f"Bearer {token}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    json=json_data,
                    params=params
                )
                response.raise_for_status()
                return response.json() if response.content else {}
                
        except httpx.HTTPStatusError as e:
            # ✅ FIX: Properly propagate HTTP status codes instead of converting everything to 503
            status_code = e.response.status_code
            
            # Try to extract error detail from response
            try:
                error_detail = e.response.json().get("detail", str(e))
            except:
                error_detail = str(e)
            
            # Propagate common HTTP errors with their original status codes
            if status_code == 400:
                raise HTTPException(status_code=400, detail=f"Bad request: {error_detail}")
            elif status_code == 401:
                # ✅ THIS IS KEY: Propagate 401 instead of converting to 503
                raise HTTPException(status_code=401, detail=f"Unauthorized: {error_detail}")
            elif status_code == 403:
                raise HTTPException(status_code=403, detail=f"Forbidden: {error_detail}")
            elif status_code == 404:
                raise HTTPException(status_code=404, detail=f"Resource not found: {error_detail}")
            elif status_code == 409:
                raise HTTPException(status_code=409, detail=f"Conflict: {error_detail}")
            elif status_code >= 500:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Service error ({status_code}): {error_detail}"
                )
            else:
                # For other status codes, propagate them as-is
                raise HTTPException(
                    status_code=status_code,
                    detail=f"Service request failed: {error_detail}"
                )
                
        except httpx.RequestError as e:
            # Network/connection errors
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service communication error: {str(e)}"
            )
    
    def get(
        self, 
        endpoint: str, 
        headers: Optional[Dict[str, str]] = None, 
        params: Optional[Dict[str, Any]] = None, 
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make GET request"""
        return self._make_request("GET", endpoint, headers=headers, params=params, token=token)
    
    def post(
        self, 
        endpoint: str, 
        json_data: Optional[Dict[str, Any]] = None, 
        headers: Optional[Dict[str, str]] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make POST request"""
        return self._make_request("POST", endpoint, headers=headers, json_data=json_data, token=token)
    
    def put(
        self, 
        endpoint: str, 
        json_data: Optional[Dict[str, Any]] = None, 
        headers: Optional[Dict[str, str]] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make PUT request"""
        return self._make_request("PUT", endpoint, headers=headers, json_data=json_data, token=token)
    
    def delete(
        self, 
        endpoint: str, 
        headers: Optional[Dict[str, str]] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make DELETE request"""
        return self._make_request("DELETE", endpoint, headers=headers, token=token)

# Service-specific clients
users_client = ServiceClient(USERS_SERVICE_URL)
rooms_client = ServiceClient(ROOMS_SERVICE_URL)
bookings_client = ServiceClient(BOOKINGS_SERVICE_URL)
reviews_client = ServiceClient(REVIEWS_SERVICE_URL)