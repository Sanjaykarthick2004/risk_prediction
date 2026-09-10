"""Pydantic schemas for prediction requests/responses."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.assessment import InjuryHistoryData, LifestyleData, PhysiologicalData, RecoveryData, TrainingData


class PredictionRequest(BaseModel):
    athlete_id: str
    assessment_id: Optional[str] = None
    training: TrainingData
    physiological: PhysiologicalData
    recovery: RecoveryData
    lifestyle: LifestyleData
    injury_history: InjuryHistoryData


class ContributorOut(BaseModel):
    feature: str
    feature_value: float
    shap_value: float


class PredictionOut(BaseModel):
    prediction_id: str
    athlete_id: str
    assessment_id: Optional[str] = None
    probability: float
    risk_level: str
    model_version: str
    prediction_date: datetime
    top_risk_factors: List[ContributorOut]
    protective_factors: List[ContributorOut]
