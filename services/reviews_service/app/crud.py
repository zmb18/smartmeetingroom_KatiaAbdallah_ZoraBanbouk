from sqlalchemy.orm import Session
from . import models, schemas

def create_review(db: Session, rev_in: schemas.ReviewCreate, user_id: int, room_id: int):
    rev = models.Review(user_id=user_id, room_id=room_id, rating=rev_in.rating, comment=rev_in.comment)
    db.add(rev)
    db.commit()
    db.refresh(rev)
    return rev

def get_reviews_for_room(db: Session, room_id: int, include_hidden: bool = False):
    q = db.query(models.Review).filter(models.Review.room_id == room_id)
    if not include_hidden:
        q = q.filter(models.Review.hidden == False)
    return q.all()

def get_review(db: Session, review_id: int):
    return db.query(models.Review).filter(models.Review.id == review_id).first()

def flag_review(db: Session, review_id: int):
    rev = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not rev:
        return None
    rev.flagged = True
    db.commit()
    db.refresh(rev)
    return rev

def moderate_review(db: Session, review_id: int, hide: bool):
    rev = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not rev:
        return None
    rev.hidden = hide
    if not hide:
        rev.flagged = False
    db.commit()
    db.refresh(rev)
    return rev

def update_review(db: Session, review_id: int, rev_in: schemas.ReviewUpdate):
    rev = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not rev:
        return None
    data = rev_in.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(rev, field, value)
    db.commit()
    db.refresh(rev)
    return rev

def delete_review(db: Session, review_id: int):
    rev = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not rev:
        return False
    db.delete(rev)
    db.commit()
    return True

def get_reviews_for_user(db: Session, user_id: int, include_hidden: bool = False):
    q = db.query(models.Review).filter(models.Review.user_id == user_id)
    if not include_hidden:
        q = q.filter(models.Review.hidden == False)
    return q.all()
