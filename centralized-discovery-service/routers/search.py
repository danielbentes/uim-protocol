# routers/search.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.dependencies import get_db

router = APIRouter(prefix="/api/search", tags=["Search"])

@router.get("/", response_model=List[schemas.Intent])
def search_intents_by_query(
    query: str,
    db: Session = Depends(get_db)
):
    """Search intents using a natural language query."""
    intents = db.query(models.Intent).filter(
        models.Intent.description.ilike(f"%{query}%") |
        models.Intent.intent_name.ilike(f"%{query}%")
    ).all()
    return intents