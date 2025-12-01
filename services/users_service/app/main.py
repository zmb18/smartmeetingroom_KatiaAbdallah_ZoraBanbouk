"""
Users Service API

FastAPI application for managing user accounts, authentication, and user-related operations.
Handles user registration, login, profile management, role assignment, and account activation.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .deps import SessionLocal, engine
from . import models, schemas, crud, auth
from fastapi.security import OAuth2PasswordRequestForm
from common import security
from common import logging_config
from common.service_client import bookings_client
from common.error_handlers import setup_error_handlers

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Users Service",
    description="Service for managing user accounts, authentication, and user-related operations",
    version="1.0.0"
)
logging_config.setup_request_logging(app)
setup_error_handlers(app)

def get_db():
    """
    Get database session dependency.
    
    Yields:
        Session: SQLAlchemy database session
        
    Note:
        Automatically closes the session after the request is complete
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.

    NOTE:
    - Role is always forced to REGULAR for self-registration, even if the client sends "admin".
    
    Args:
        user_in: User registration data
        db: Database session
        
    Returns:
        UserOut: Created user information
        
    Raises:
        HTTPException: 400 if username or email already exists
    """

    if crud.get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if crud.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")

   
    safe_user = schemas.UserCreate(
        username=user_in.username,
        password=user_in.password,
        email=user_in.email,
        full_name=user_in.full_name,
        role=security.ROLE_REGULAR,
    )

    user = crud.create_user(db, safe_user)
    return user

@app.post("/token", response_model=schemas.Token)
def login_for_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT access token.
    
    Args:
        form_data: OAuth2 password form with username and password
        db: Database session
        
    Returns:
        Token: Access token and token type
        
    Raises:
        HTTPException: 401 if credentials are incorrect
    """
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
    token = auth.create_access_token({"sub": user.username, "user_id": user.id,"role": user.role})
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User: Current authenticated user object
        
    Raises:
        HTTPException: 401 if token is invalid or user not found, 403 if user is deactivated
    """
    payload = auth.decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid auth")
    
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
   
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is deactivated")
    
    return user


@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserOut: Current user's information
    """
    return current_user

@app.get("/health")
def health():
    """
    Health check endpoint.
    
    Returns:
        dict: Status indicating service is running
    """
    return {"status": "ok"}

@app.get("/users", response_model=list[schemas.UserOut])
def read_users(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    List all users. Only Admin and Auditor roles can access this endpoint.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        list[UserOut]: List of all users
        
    Raises:
        HTTPException: 403 if user is not Admin or Auditor
    """
    if current_user.role not in (security.ROLE_ADMIN, security.ROLE_AUDITOR):
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.list_users(db)

@app.get("/users/{username}", response_model=schemas.UserOut)
def read_user(username: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Get user by username. Users can view their own profile, or Admin/Auditor can view any user.
    
    Args:
        username: Username of the user to retrieve
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        UserOut: User information
        
    Raises:
        HTTPException: 403 if not authorized, 404 if user not found
    """
    if current_user.username != username and current_user.role not in (security.ROLE_ADMIN, security.ROLE_AUDITOR):
        raise HTTPException(status_code=403, detail="Not authorized")
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{username}", response_model=schemas.UserOut)
def update_user(
    username: str,
    user_in: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Update user profile.
    - Regular/Manager/Moderator/Service can update ONLY their own profile (no role changes).
    - Admin can update any user and may change roles.
    - Auditor is strictly read-only and cannot update anything.
    
    Args:
        username: Username of the user to update
        user_in: User update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        UserOut: Updated user information
        
    Raises:
        HTTPException: 403 if not authorized, 404 if user not found
    """
 
    if current_user.role == security.ROLE_AUDITOR:
        raise HTTPException(status_code=403, detail="Auditor role is read-only")


    if current_user.username != username and current_user.role != security.ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    if current_user.role != security.ROLE_ADMIN:
        sanitized = schemas.UserUpdate(
            email=user_in.email,
            full_name=user_in.full_name,
            password=user_in.password,
            role=None,  
        )
        user = crud.update_user(db, username, sanitized)
    else:
     
        user = crud.update_user(db, username, user_in)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@app.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    username: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Delete user account.
    - User can delete their own account.
    - Admin can delete any account.
    - Auditor is read-only and cannot delete.
    
    Args:
        username: Username of the user to delete
        db: Database session
        current_user: Current authenticated user
        
    Raises:
        HTTPException: 403 if not authorized, 404 if user not found
    """

    if current_user.role == security.ROLE_AUDITOR:
        raise HTTPException(status_code=403, detail="Auditor role is read-only")

    if current_user.username != username and current_user.role != security.ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    deleted = crud.delete_user(db, username)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

@app.get("/users/{username}/bookings", response_model=list[dict])
def get_user_booking_history(username: str, db: Session = Depends(get_db), current_user = Depends(get_current_user), token: str = Depends(auth.oauth2_scheme)):
    """
    Get user's booking history. Users can view their own history, or Admin/Auditor can view any user's history.
    
    Args:
        username: Username of the user
        db: Database session
        current_user: Current authenticated user
        token: JWT token for inter-service calls
        
    Returns:
        list[dict]: List of bookings for the user
        
    Raises:
        HTTPException: 403 if not authorized, 404 if user not found, 503 if bookings service unavailable
    """
    if current_user.username != username and current_user.role not in (security.ROLE_ADMIN, security.ROLE_AUDITOR):
        raise HTTPException(status_code=403, detail="Not authorized")
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    
    try:
        bookings = bookings_client.get(f"/bookings/user/{user.id}", token=token)
        return bookings if isinstance(bookings, list) else []
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to get booking history: {str(e)}")

@app.put("/users/{username}/password", response_model=schemas.UserOut)
def reset_user_password(
    username: str,
    password_reset: schemas.PasswordReset,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Reset a user's password. Only Admin can reset passwords.
    
    Args:
        username: Username of the user
        password_reset: New password data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        UserOut: Updated user information
        
    Raises:
        HTTPException: 403 if not admin, 404 if user not found
    """
    if current_user.role != security.ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can reset passwords")

    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")


    user.hashed_password = auth.hash_password(password_reset.new_password)
    db.commit()
    db.refresh(user)
    return user


@app.put("/users/{username}/role", response_model=schemas.UserOut)
def assign_user_role(username: str, role_update: schemas.RoleUpdate, 
                     db: Session = Depends(get_db), 
                     current_user = Depends(get_current_user)):
    """
    Assign a new role to a user. Only Admin can assign roles.
    
    Args:
        username: Username of the user
        role_update: New role data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        UserOut: Updated user information
        
    Raises:
        HTTPException: 403 if not admin, 400 if trying to change own role, 404 if user not found
    """
    if current_user.role != security.ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can assign roles")
    
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    

    if user.id == current_user.id and role_update.role != security.ROLE_ADMIN:
        raise HTTPException(status_code=400, detail="Cannot change your own admin role")
    
    user.role = role_update.role
    db.commit()
    db.refresh(user)
    return user

@app.put("/users/{username}/deactivate", response_model=schemas.UserOut)
def deactivate_user(username: str, db: Session = Depends(get_db), 
                    current_user = Depends(get_current_user)):
    """
    Deactivate user account. Only Admin can deactivate accounts.
    
    Args:
        username: Username of the user to deactivate
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        UserOut: Updated user information
        
    Raises:
        HTTPException: 403 if not admin, 400 if trying to deactivate own account, 404 if user not found
    """
    if current_user.role != security.ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can deactivate accounts")
    
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
 
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user

@app.put("/users/{username}/activate", response_model=schemas.UserOut)
def activate_user(username: str, db: Session = Depends(get_db), 
                  current_user = Depends(get_current_user)):
    """
    Activate user account. Only Admin can activate accounts.
    
    Args:
        username: Username of the user to activate
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        UserOut: Updated user information
        
    Raises:
        HTTPException: 403 if not admin, 404 if user not found
    """
    if current_user.role != security.ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can activate accounts")
    
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user