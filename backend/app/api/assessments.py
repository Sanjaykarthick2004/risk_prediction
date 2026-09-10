"""Assessment endpoints, nested under an athlete. Scoped to the requesting researcher."""
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.schemas.assessment import AssessmentCreate
from app.services import assessment_service

router = APIRouter(prefix="/api", tags=["assessments"])


@router.get("/athletes/{athlete_id}/assessments")
def list_assessments(athlete_id: str, user=Depends(get_current_user)):
    return assessment_service.list_assessments_for_athlete(athlete_id, user["username"])


@router.post("/athletes/{athlete_id}/assessments", status_code=201)
def create_assessment(athlete_id: str, payload: AssessmentCreate, user=Depends(get_current_user)):
    return assessment_service.create_assessment(athlete_id, payload, user["username"])


@router.get("/assessments/{assessment_id}")
def get_assessment(assessment_id: str, user=Depends(get_current_user)):
    return assessment_service.get_assessment(assessment_id, user["username"])
