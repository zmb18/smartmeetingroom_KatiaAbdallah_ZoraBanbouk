from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .deps import SessionLocal, engine
from . import models, schemas, crud, auth
from common import security
from common import logging_config
from common.service_client import users_client, rooms_client
from common.error_handlers import setup_error_handlers

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Reviews Service",
    description="Service for managing room reviews, ratings, and review moderation",
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

def get_token_data(token: str = Depends(auth.oauth2_scheme)):
    return auth.decode_token(token)

def get_token_string(token: str = Depends(auth.oauth2_scheme)) -> str:
    """Get the raw token string for passing to other services"""
    return token

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/rooms/{room_id}/reviews", response_model=schemas.ReviewOut)
def post_review(room_id: int, rev_in: schemas.ReviewCreate, db: Session = Depends(get_db), token_data = Depends(get_token_data), token: str = Depends(get_token_string)):
    # Ensure authenticated
    username = token_data.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get user_id from users service
    try:
        user_data = users_client.get(f"/users/{username}", token=token)
        user_id = user_data.get("id")
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to get user info: {str(e)}")
    
    # Validate room exists
    try:
        room_data = rooms_client.get(f"/rooms/{room_id}")
        if not room_data.get("is_active", False):
            raise HTTPException(status_code=400, detail="Room is not active")
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Room not found")
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to validate room: {str(e)}")
    
    # Create review with user_id from token
    return crud.create_review(db, rev_in, user_id=user_id, room_id=room_id)

@app.get("/rooms/{room_id}/reviews", response_model=list[schemas.ReviewOut])
def get_reviews(room_id: int, db: Session = Depends(get_db)):
    return crud.get_reviews_for_room(db, room_id)

@app.post("/reviews/{review_id}/flag", response_model=schemas.ReviewOut)
def flag(review_id: int, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    return crud.flag_review(db, review_id)

@app.put("/reviews/{review_id}/moderate", response_model=schemas.ReviewOut)
def moderate(review_id: int, hide: bool, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    security.require_any_role(token_data, {security.ROLE_ADMIN, security.ROLE_MODERATOR})
    res = crud.moderate_review(db, review_id, hide)
    if not res:
        raise HTTPException(status_code=404, detail="Review not found")
    return res

@app.put("/reviews/{review_id}", response_model=schemas.ReviewOut)
def update_review(review_id: int, rev_in: schemas.ReviewUpdate, db: Session = Depends(get_db), token_data = Depends(get_token_data), token: str = Depends(get_token_string)):
    role = token_data.get("role")
    username = token_data.get("sub")
    existing = crud.get_review(db, review_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check authorization: admin/moderator or owner
    if role not in (security.ROLE_ADMIN, security.ROLE_MODERATOR):
        # Verify this is the user's own review
        try:
            user_data = users_client.get(f"/users/{username}", token=token)
            if user_data.get("id") != existing.user_id:
                raise HTTPException(status_code=403, detail="Not authorized to update this review")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    updated = crud.update_review(db, review_id, rev_in)
    return updated

@app.delete("/reviews/{review_id}", status_code=204)
def delete_review(review_id: int, db: Session = Depends(get_db), token_data = Depends(get_token_data), token: str = Depends(get_token_string)):
    role = token_data.get("role")
    username = token_data.get("sub")
    existing = crud.get_review(db, review_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check authorization: admin/moderator or owner
    if role not in (security.ROLE_ADMIN, security.ROLE_MODERATOR):
        # Verify this is the user's own review
        try:
            user_data = users_client.get(f"/users/{username}", token=token)
            if user_data.get("id") != existing.user_id:
                raise HTTPException(status_code=403, detail="Not authorized to delete this review")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    deleted = crud.delete_review(db, review_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Review not found")
    return None

@app.get("/users/{user_id}/reviews", response_model=list[schemas.ReviewOut])
def list_reviews_for_user(user_id: int, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    return crud.get_reviews_for_user(db, user_id)
