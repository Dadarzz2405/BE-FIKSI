from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
class User(Base):
    id=Column(
        Integer, 
        primary_key=True, 
        index=True
    )
    real_name=Column(
        String, 
        index=True
    )
    username=Column(
        String, 
        unique=True, 
        index=True
    )
    email=Column(
        String, 
        unique=True, 
        index=True
    )
    hashed_password=Column(String)
    is_active=Column(
        Boolean, 
        default=False
    )
    subscription=Column(
        String, 
        default="Free"
    )
    created_at=Column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at=Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    bio=Column(
        String(100), 
        default=""
    )