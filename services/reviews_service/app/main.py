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
def post_review(room_id: int, rev_in: schemas.ReviewCreate, db: Session = Depends(get_db), 
                token_data = Depends(get_token_data), token: str = Depends(get_token_string)):
    """
    Submit a review for a meeting room. User ID is extracted from JWT token.
    
    Args:
        room_id: ID of the room to review
        rev_in: Review details (rating, comment)
        db: Database session
        token_data: Decoded JWT token data
        token: Raw JWT token for inter-service calls
        
    Returns:
        ReviewOut: Created review
        
    Raises:
        HTTPException: 401 if not authenticated, 404 if user/room not found, 400 if room inactive
    """
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
    """
    Get all reviews for a specific room. Only non-hidden reviews are returned for regular users.
    
    Args:
        room_id: ID of the room
        db: Database session
        
    Returns:
        list[ReviewOut]: List of reviews for the room
    """
    return crud.get_reviews_for_room(db, room_id)

@app.post("/reviews/{review_id}/flag", response_model=schemas.ReviewOut)
def flag(review_id: int, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    """
    Flag a review as inappropriate. Any authenticated user can flag reviews.
    
    Args:
        review_id: ID of the review to flag
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        ReviewOut: Flagged review
        
    Raises:
        HTTPException: 404 if review not found
    """
    review = crud.flag_review(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

@app.post("/reviews/{review_id}/unflag", response_model=schemas.ReviewOut)
def unflag(review_id: int, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    """
    Unflag a review. Only Admin and Moderator roles can unflag.
    
    Args:
        review_id: ID of the review to unflag
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        ReviewOut: Unflagged review
        
    Raises:
        HTTPException: 403 if not authorized, 404 if review not found
    """
    security.require_any_role(token_data, {security.ROLE_ADMIN, security.ROLE_MODERATOR})
    review = crud.get_review(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.flagged = False
    db.commit()
    db.refresh(review)
    return review

@app.get("/reviews/flagged", response_model=list[schemas.ReviewOut])
def get_flagged_reviews(db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    """
    Get all flagged reviews for moderation. Only Admin, Moderator, and Manager roles can access.
    
    Args:
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        list[ReviewOut]: List of flagged reviews
        
    Raises:
        HTTPException: 403 if not authorized
    """
    security.require_any_role(token_data, {security.ROLE_ADMIN, security.ROLE_MODERATOR, security.ROLE_MANAGER})
    return db.query(models.Review).filter(models.Review.flagged == True).all()

@app.get("/reviews/hidden", response_model=list[schemas.ReviewOut])
def get_hidden_reviews(db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    """
    Get all hidden reviews. Only Admin and Moderator roles can access.
    
    Args:
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        list[ReviewOut]: List of hidden reviews
        
    Raises:
        HTTPException: 403 if not authorized
    """
    security.require_any_role(token_data, {security.ROLE_ADMIN, security.ROLE_MODERATOR})
    return db.query(models.Review).filter(models.Review.hidden == True).all()

@app.put("/reviews/{review_id}/moderate", response_model=schemas.ReviewOut)
def moderate(review_id: int, hide: bool, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    """
    Moderate a review by hiding or unhiding it. Only Admin, Moderator, and Manager roles can moderate.
    
    Args:
        review_id: ID of the review to moderate
        hide: True to hide the review, False to unhide
        db: Database session
        token_data: Decoded JWT token data
        
    Returns:
        ReviewOut: Moderated review
        
    Raises:
        HTTPException: 403 if not authorized, 404 if review not found
    """
    security.require_any_role(token_data, {security.ROLE_ADMIN, security.ROLE_MODERATOR, security.ROLE_MANAGER})
    res = crud.moderate_review(db, review_id, hide)
    if not res:
        raise HTTPException(status_code=404, detail="Review not found")
    return res

@app.put("/reviews/{review_id}", response_model=schemas.ReviewOut)
def update_review(review_id: int, rev_in: schemas.ReviewUpdate, db: Session = Depends(get_db), 
                  token_data = Depends(get_token_data), token: str = Depends(get_token_string)):
    """
    Update a review. Users can update their own reviews, Admin and Moderator can update any review.
    
    Args:
        review_id: ID of the review to update
        rev_in: Updated review data (rating, comment)
        db: Database session
        token_data: Decoded JWT token data
        token: Raw JWT token for inter-service calls
        
    Returns:
        ReviewOut: Updated review
        
    Raises:
        HTTPException: 403 if not authorized, 404 if review not found
    """
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
def delete_review(review_id: int, db: Session = Depends(get_db), 
                  token_data = Depends(get_token_data), token: str = Depends(get_token_string)):
    """
    Delete a review. Users can delete their own reviews, Admin and Moderator can delete any review.
    
    Args:
        review_id: ID of the review to delete
        db: Database session
        token_data: Decoded JWT token data
        token: Raw JWT token for inter-service calls
        
    Returns:
        None (204 No Content)
        
    Raises:
        HTTPException: 403 if not authorized, 404 if review not found
    """
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
def list_reviews_for_user(user_id: int, db: Session = Depends(get_db), 
                          token_data = Depends(get_token_data), token: str = Depends(get_token_string)):
    """
    Get all reviews submitted by a specific user. Users can view their own reviews, 
    Admin/Moderator/Auditor/Manager can view any user's reviews.
    
    Args:
        user_id: ID of the user
        db: Database session
        token_data: Decoded JWT token data
        token: Raw JWT token for inter-service calls
        
    Returns:
        list[ReviewOut]: List of reviews by the user
        
    Raises:
        HTTPException: 403 if not authorized
    """
    role = token_data.get("role")
    username = token_data.get("sub")
    
    # Authorization check
    if role not in (security.ROLE_ADMIN, security.ROLE_MODERATOR, security.ROLE_AUDITOR, security.ROLE_MANAGER):
        # Verify this is the user's own reviews
        try:
            user_data = users_client.get(f"/users/{username}", token=token)
            if user_data.get("id") != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to view this user's reviews")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.get_reviews_for_user(db, user_id)