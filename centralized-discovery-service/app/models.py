# app/models.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base

intent_tags = Table(
    'intent_tags',
    Base.metadata,
    Column('intent_id', Integer, ForeignKey('intents.id')),
    Column('tag', String, index=True)
)

class Service(Base):
    """Service model representing an intent provider."""
    __tablename__ = 'services'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    service_url = Column(String)
    intents = relationship('Intent', back_populates='service')

class Intent(Base):
    """Intent model representing a single intent."""
    __tablename__ = 'intents'
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey('services.id'))
    intent_uid = Column(String, unique=True, index=True)
    intent_name = Column(String, index=True)
    description = Column(Text)
    input_parameters = Column(JSONB)
    output_parameters = Column(JSONB)
    endpoint = Column(String)
    tags = relationship('Tag', secondary=intent_tags, back_populates='intents')
    service = relationship('Service', back_populates='intents')

class Tag(Base):
    """Tag model for intent categorization."""
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    intents = relationship('Intent', secondary=intent_tags, back_populates='tags')