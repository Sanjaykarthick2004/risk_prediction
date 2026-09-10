"""Pydantic schemas for athlete assessments (the six data modalities)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TrainingData(BaseModel):
    training_hours_per_week: float = Field(..., ge=0, le=30)
    training_frequency: int = Field(..., ge=0, le=14)
    training_intensity: int = Field(..., ge=1, le=10)
    weekly_distance_km: float = Field(..., ge=0, le=200)
    long_run_distance_km: float = Field(..., ge=0, le=50)
    speed_work_sessions: int = Field(..., ge=0, le=10)
    training_load: float = Field(..., ge=0, le=3000)
    acute_training_load: float = Field(..., ge=0, le=3000)
    chronic_training_load: float = Field(..., ge=0, le=3000)


class PhysiologicalData(BaseModel):
    resting_heart_rate: float = Field(..., ge=30, le=120)
    heart_rate_variability: float = Field(..., ge=0, le=200)
    fatigue_score: int = Field(..., ge=1, le=10)
    muscle_soreness: int = Field(..., ge=1, le=10)
    recovery_score: float = Field(..., ge=0, le=100)


class RecoveryData(BaseModel):
    sleep_hours: float = Field(..., ge=0, le=16)
    sleep_quality: int = Field(..., ge=1, le=10)
    recovery_days: int = Field(..., ge=0, le=14)
    rest_days: int = Field(..., ge=0, le=14)


class LifestyleData(BaseModel):
    stress_level: int = Field(..., ge=1, le=10)
    hydration_score: float = Field(..., ge=0, le=100)
    nutrition_score: float = Field(..., ge=0, le=100)


class InjuryHistoryData(BaseModel):
    previous_injury: int = Field(..., ge=0, le=1)
    injury_count: int = Field(..., ge=0, le=20)
    previous_injury_type: str = "None"
    days_since_previous_injury: int = Field(..., ge=0, le=3650)
    previous_recovery_duration: int = Field(..., ge=0, le=365)


class AssessmentCreate(BaseModel):
    training: TrainingData
    physiological: PhysiologicalData
    recovery: RecoveryData
    lifestyle: LifestyleData
    injury_history: InjuryHistoryData


class AssessmentOut(AssessmentCreate):
    assessment_id: str
    athlete_id: str
    assessment_date: datetime
    demographic: Optional[dict] = None
