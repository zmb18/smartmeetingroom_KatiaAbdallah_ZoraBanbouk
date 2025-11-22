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
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Args:
        user_in: User registration data (username, password, email, full_name, role)
        db: Database session
        
    Returns:
        UserOut: Created user object (without password)
        
    Raises:
        HTTPException: 400 if username or email already exists
    """
    if crud.get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if crud.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db, user_in)
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
    token = auth.create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    payload = auth.decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid auth")
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    
    Returns:
        UserOut: Current user's information
    """
    return current_user

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/users", response_model=list[schemas.UserOut])
def read_users(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    List all users. Only Admin and Auditor roles can access this endpoint.
    
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
def update_user(username: str, user_in: schemas.UserUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Update user profile. Users can update their own profile, or Admin can update any user.
    
    Args:
        username: Username of the user to update
        user_in: Updated user information
        
    Returns:
        UserOut: Updated user information
        
    Raises:
        HTTPException: 403 if not authorized, 404 if user not found
    """
    if current_user.username != username and current_user.role not in (security.ROLE_ADMIN,):
        raise HTTPException(status_code=403, detail="Not authorized")
    user = crud.update_user(db, username, user_in)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(username: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Delete user account. Users can delete their own account, or Admin can delete any user.
    
    Args:
        username: Username of the user to delete
        
    Returns:
        None
        
    Raises:
        HTTPException: 403 if not authorized, 404 if user not found
    """
    if current_user.username != username and current_user.role not in (security.ROLE_ADMIN,):
        raise HTTPException(status_code=403, detail="Not authorized")
    deleted = crud.delete_user(db, username)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return None

@app.get("/users/{username}/bookings", response_model=list[dict])
def get_user_booking_history(username: str, db: Session = Depends(get_db), current_user = Depends(get_current_user), token: str = Depends(auth.oauth2_scheme)):
    """
    Get user's booking history. Users can view their own history, or Admin/Auditor can view any user's history.
    
    Args:
        username: Username of the user
        
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
    
    # Get booking history from bookings service
    try:
        bookings = bookings_client.get(f"/bookings/user/{user.id}", token=token)
        return bookings if isinstance(bookings, list) else []
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to get booking history: {str(e)}")
