from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .deps import SessionLocal, engine
from . import models, schemas, crud, auth
from common import security
from common import logging_config

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Reviews Service")
logging_config.setup_request_logging(app)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_token_data(token: str = Depends(auth.oauth2_scheme)):
    return auth.decode_token(token)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/rooms/{room_id}/reviews", response_model=schemas.ReviewOut)
def post_review(room_id: int, rev_in: schemas.ReviewCreate, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    # ensure authenticated
    if token_data.get("sub") is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    # ensure user_id in payload matches token (in full system) - simplified here
    if rev_in.room_id != room_id:
        raise HTTPException(status_code=400, detail="room_id mismatch")
    return crud.create_review(db, rev_in)

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
def update_review(review_id: int, rev_in: schemas.ReviewUpdate, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    role = token_data.get("role")
    actor = token_data.get("sub")
    existing = crud.get_review(db, review_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Review not found")
    # Basic authorization: admin/moderator or owner (assuming sub carries user_id as string)
    if role not in (security.ROLE_ADMIN, security.ROLE_MODERATOR) and str(existing.user_id) != str(actor):
        raise HTTPException(status_code=403, detail="Not authorized")
    updated = crud.update_review(db, review_id, rev_in)
    return updated

@app.delete("/reviews/{review_id}", status_code=204)
def delete_review(review_id: int, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    role = token_data.get("role")
    actor = token_data.get("sub")
    existing = crud.get_review(db, review_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Review not found")
    if role not in (security.ROLE_ADMIN, security.ROLE_MODERATOR) and str(existing.user_id) != str(actor):
        raise HTTPException(status_code=403, detail="Not authorized")
    deleted = crud.delete_review(db, review_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Review not found")
    return None

@app.get("/users/{user_id}/reviews", response_model=list[schemas.ReviewOut])
def list_reviews_for_user(user_id: int, db: Session = Depends(get_db), token_data = Depends(get_token_data)):
    return crud.get_reviews_for_user(db, user_id)
