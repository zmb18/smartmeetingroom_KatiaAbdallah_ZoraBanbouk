from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .deps import SessionLocal, engine
from . import models, schemas, crud, auth
from fastapi.security import OAuth2PasswordRequestForm
from common import security
from common import logging_config

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Users Service")
logging_config.setup_request_logging(app)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if crud.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db, user_in)
    return user

@app.post("/token", response_model=schemas.Token)
def login_for_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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
    return current_user

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/users", response_model=list[schemas.UserOut])
def read_users(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role not in (security.ROLE_ADMIN, security.ROLE_AUDITOR):
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.list_users(db)

@app.get("/users/{username}", response_model=schemas.UserOut)
def read_user(username: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # allow self or admin/auditor
    if current_user.username != username and current_user.role not in (security.ROLE_ADMIN, security.ROLE_AUDITOR):
        raise HTTPException(status_code=403, detail="Not authorized")
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{username}", response_model=schemas.UserOut)
def update_user(username: str, user_in: schemas.UserUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # self or admin can update
    if current_user.username != username and current_user.role not in (security.ROLE_ADMIN,):
        raise HTTPException(status_code=403, detail="Not authorized")
    user = crud.update_user(db, username, user_in)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(username: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.username != username and current_user.role not in (security.ROLE_ADMIN,):
        raise HTTPException(status_code=403, detail="Not authorized")
    deleted = crud.delete_user(db, username)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return None

@app.get("/users/{username}/bookings", response_model=list[dict])
def get_user_booking_history(username: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Placeholder: booking history would come from bookings service; here we return stored metadata if any
    if current_user.username != username and current_user.role not in (security.ROLE_ADMIN, security.ROLE_AUDITOR):
        raise HTTPException(status_code=403, detail="Not authorized")
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.metadata or []
