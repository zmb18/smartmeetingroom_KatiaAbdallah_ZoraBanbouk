# auth.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

# -----------------------------
# Password hashing configuration
# -----------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_BCRYPT_LENGTH = 72  # bcrypt limitation

def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt, truncating if >72 bytes.
    """
    truncated = password.encode("utf-8")[:MAX_BCRYPT_LENGTH].decode("utf-8", "ignore")
    return pwd_context.hash(truncated)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    """
    truncated = plain_password.encode("utf-8")[:MAX_BCRYPT_LENGTH].decode("utf-8", "ignore")
    return pwd_context.verify(truncated, hashed_password)

# -----------------------------
# JWT / Token utilities
# -----------------------------
SECRET_KEY = "your-secret-key"  # change this to a strong random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    """
    Decode a JWT token and return the payload.
    Raises JWTError if invalid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise e

# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    pwd = "thisIsAReallyLongPasswordThatExceedsThe72ByteLimitSetByBcrypt" * 2
    hashed = hash_password(pwd)
    print("Hashed password:", hashed)
    print("Verify:", verify_password(pwd, hashed))
