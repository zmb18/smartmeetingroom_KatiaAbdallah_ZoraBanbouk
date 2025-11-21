import os
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "devsecret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except (ExpiredSignatureError, JWTError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
