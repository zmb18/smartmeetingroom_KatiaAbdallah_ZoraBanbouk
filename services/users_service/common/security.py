from fastapi import HTTPException, status

# Role constants
ROLE_ADMIN = "admin"
ROLE_REGULAR = "regular"
ROLE_MANAGER = "manager"
ROLE_MODERATOR = "moderator"
ROLE_AUDITOR = "auditor"
ROLE_SERVICE = "service"


def require_role(token_data: dict, *allowed_roles: str):
    role = token_data.get("role")
    if role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


def require_any_role(token_data: dict, allowed_roles: set[str] | list[str]):
    role = token_data.get("role")
    if role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
