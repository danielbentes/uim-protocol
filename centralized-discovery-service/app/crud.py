# app/crud.py

from sqlalchemy.orm import Session
from app import models, schemas

def get_intent_by_uid(db: Session, intent_uid: str):
    """Retrieve intent by UID."""
    return db.query(models.Intent).filter(models.Intent.intent_uid == intent_uid).first()

def create_service(db: Session, service_info: schemas.ServiceInfo):
    """Create a new service."""
    db_service = models.Service(
        name=service_info.name,
        description=service_info.description,
        service_url=service_info.service_url
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def create_intent(db: Session, intent_data: schemas.Intent, service_id: int):
    """Create a new intent."""
    db_intent = models.Intent(
        service_id=service_id,
        intent_uid=intent_data.intent_uid,
        intent_name=intent_data.intent_name,
        description=intent_data.description,
        input_parameters=intent_data.input_parameters,
        output_parameters=intent_data.output_parameters,
        endpoint=intent_data.endpoint
    )
    db.add(db_intent)
    db.commit()
    db.refresh(db_intent)
    return db_intent