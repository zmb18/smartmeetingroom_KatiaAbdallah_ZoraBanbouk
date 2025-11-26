import os
from datetime import datetime, timedelta
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any, Optional

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "devsecret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token.

    This function attempts to decode a JWT token using the configured
    SECRET_KEY and algorithm. If the token is expired or invalid,
    it raises an HTTP 401 Unauthorized exception.

    Args:
        token (str): The JWT token to decode.

    Returns:
        Dict[str, Any]: The payload inside the JWT token.

    Raises:
        HTTPException: If the token is invalid, expired, or cannot be decoded.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except (ExpiredSignatureError, JWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT access token.

    This function generates a JWT token using the provided data and applies
    an expiration time. If no custom expiration is provided, it uses the
    default duration defined in ACCESS_TOKEN_EXPIRE_MINUTES.

    Args:
        data (Dict[str, Any]): The payload to include in the token.
        expires_delta (Optional[timedelta], optional): Custom expiration duration.
            Defaults to None.

    Returns:
        str: The encoded JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
