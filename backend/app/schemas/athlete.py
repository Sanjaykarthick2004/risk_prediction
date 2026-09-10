"""Pydantic schemas for athlete profile records."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AthleteCreate(BaseModel):
    athlete_id: Optional[str] = Field(None, max_length=30)  # auto-generated (ATH-0001, ...) if omitted
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=15, le=60)
    gender: str
    sport: str
    event_type: str
    height: float = Field(..., ge=100, le=230)
    weight: float = Field(..., ge=30, le=200)
    experience_years: float = Field(..., ge=0, le=45)


class AthleteUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=15, le=60)
    gender: Optional[str] = None
    sport: Optional[str] = None
    event_type: Optional[str] = None
    height: Optional[float] = Field(None, ge=100, le=230)
    weight: Optional[float] = Field(None, ge=30, le=200)
    experience_years: Optional[float] = Field(None, ge=0, le=45)


class AthleteOut(AthleteCreate):
    created_at: datetime
    updated_at: datetime
