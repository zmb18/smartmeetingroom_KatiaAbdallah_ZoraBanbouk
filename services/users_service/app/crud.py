from sqlalchemy.orm import Session
from . import models, schemas
from .auth import hash_password

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user_in: schemas.UserCreate):
    hashed = hash_password(user_in.password)
    user = models.User(username=user_in.username, hashed_password=hashed, email=user_in.email, full_name=user_in.full_name, role=user_in.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def list_users(db: Session):
    return db.query(models.User).all()

def update_user(db: Session, username: str, user_in: schemas.UserUpdate):
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
    user = get_user_by_username(db, username)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
