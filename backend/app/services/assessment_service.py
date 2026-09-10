"""Assessment CRUD operations against MongoDB. Scoped to the owning researcher."""
from typing import List

from fastapi import HTTPException

from app.database.mongodb import assessments_collection
from app.schemas.assessment import AssessmentCreate
from app.services.athlete_service import get_athlete
from app.utils.helpers import new_id, utcnow


def create_assessment(athlete_id: str, payload: AssessmentCreate, owner: str) -> dict:
    athlete = get_athlete(athlete_id, owner)  # raises 404 if missing or not owned by this user

    demographic_snapshot = {
        "age": athlete["age"],
        "gender": athlete["gender"],
        "sport": athlete["sport"],
        "event_type": athlete["event_type"],
        "height": athlete["height"],
        "weight": athlete["weight"],
        "experience_years": athlete["experience_years"],
    }

    doc = payload.model_dump()
    doc["assessment_id"] = new_id("ASM")
    doc["athlete_id"] = athlete_id
    doc["created_by"] = owner
    doc["assessment_date"] = utcnow()
    doc["demographic"] = demographic_snapshot

    assessments_collection.insert_one(doc)
    return get_assessment(doc["assessment_id"], owner)


def list_assessments_for_athlete(athlete_id: str, owner: str) -> List[dict]:
    cursor = assessments_collection.find(
        {"athlete_id": athlete_id, "created_by": owner}, {"_id": 0},
    ).sort("assessment_date", -1)
    return list(cursor)


def get_assessment(assessment_id: str, owner: str) -> dict:
    doc = assessments_collection.find_one({"assessment_id": assessment_id, "created_by": owner}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found")
    return doc
