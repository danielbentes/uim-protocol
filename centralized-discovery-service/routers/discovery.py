# routers/discovery.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.dependencies import get_db

router = APIRouter(prefix="/api/intents", tags=["Discovery"])

@router.get("/search", response_model=List[schemas.Intent])
def search_intents(
    intent_name: str = None,
    uid: str = None,
    description: str = None,
    tags: str = None,
    db: Session = Depends(get_db)
):
    """Search for intents based on criteria."""
    query = db.query(models.Intent)
    if intent_name:
        query = query.filter(models.Intent.intent_name.ilike(f"%{intent_name}%"))
    if uid:
        query = query.filter(models.Intent.intent_uid == uid)
    if description:
        query = query.filter(models.Intent.description.ilike(f"%{description}%"))
    if tags:
        tag_list = tags.split(',')
        query = query.filter(models.Intent.tags.any(models.Tag.name.in_(tag_list)))
    return query.all()