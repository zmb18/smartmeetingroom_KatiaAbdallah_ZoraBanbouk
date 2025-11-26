"""
CRUD operations for the Users service.

This module provides database operations for user management including
creation, retrieval, updates, and deletion of user records.
"""

from sqlalchemy.orm import Session
from . import models, schemas
from .auth import hash_password

def get_user_by_username(db: Session, username: str):
    """
    Retrieve a user by username.
    
    Args:
        db: Database session
        username: Username to search for
        
    Returns:
        User: User object if found, None otherwise
    """
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    """
    Retrieve a user by email address.
    
    Args:
        db: Database session
        email: Email address to search for
        
    Returns:
        User: User object if found, None otherwise
    """
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user_in: schemas.UserCreate):
    """
    Create a new user in the database.
    
    Args:
        db: Database session
        user_in: User creation schema with username, password, email, full_name, and role
        
    Returns:
        User: Newly created user object
    """
    hashed = hash_password(user_in.password)
    user = models.User(username=user_in.username, hashed_password=hashed, email=user_in.email, full_name=user_in.full_name, role=user_in.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def list_users(db: Session):
    """
    List all users in the database.
    
    Args:
        db: Database session
        
    Returns:
        list[User]: List of all user objects
    """
    return db.query(models.User).all()

def update_user(db: Session, username: str, user_in: schemas.UserUpdate):
    """
    Update an existing user's information.
    
    Args:
        db: Database session
        username: Username of the user to update
        user_in: User update schema with optional fields (email, full_name, role, password)
        
    Returns:
        User: Updated user object if found, None otherwise
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.password is not None:
        user.hashed_password = hash_password(user_in.password)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, username: str):
    """
    Delete a user from the database.
    
    Args:
        db: Database session
        username: Username of the user to delete
        
    Returns:
        bool: True if user was deleted, False if user was not found
    """
    user = get_user_by_username(db, username)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True