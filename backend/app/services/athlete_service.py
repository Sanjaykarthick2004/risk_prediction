"""Athlete CRUD operations against MongoDB.

Every athlete is owned by the researcher who created it (`created_by`) — one
account's athletes, assessments, and predictions are never visible to another
account. This is enforced here, not just in the UI.
"""
import re
from typing import List, Optional

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.database.mongodb import athletes_collection
from app.schemas.athlete import AthleteCreate, AthleteUpdate
from app.utils.helpers import utcnow

ATHLETE_ID_PATTERN = re.compile(r"^ATH-(\d+)$")


def _generate_athlete_id() -> str:
    """Next sequential ATH-0001, ATH-0002, ... based on the highest existing numeric suffix
    across ALL accounts, so ids stay globally unique even though data is per-owner.
    """
    max_num = 0
    for doc in athletes_collection.find({"athlete_id": {"$regex": r"^ATH-\d+$"}}, {"athlete_id": 1}):
        match = ATHLETE_ID_PATTERN.match(doc["athlete_id"])
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"ATH-{max_num + 1:04d}"


def create_athlete(payload: AthleteCreate, owner: str) -> dict:
    athlete_id = (payload.athlete_id or "").strip() or None

    if athlete_id:
        if athletes_collection.find_one({"athlete_id": athlete_id}):
            raise HTTPException(status_code=409, detail=f"Athlete '{athlete_id}' already exists")
    else:
        athlete_id = _generate_athlete_id()

    now = utcnow()
    doc = payload.model_dump()
    doc["athlete_id"] = athlete_id
    doc["created_by"] = owner
    doc["created_at"] = now
    doc["updated_at"] = now

    try:
        athletes_collection.insert_one(doc)
    except DuplicateKeyError:
        if payload.athlete_id:
            raise HTTPException(status_code=409, detail=f"Athlete '{athlete_id}' already exists") from None
        # Auto-generated id collided with one inserted concurrently — regenerate once and retry.
        doc["athlete_id"] = _generate_athlete_id()
        athletes_collection.insert_one(doc)

    return get_athlete(doc["athlete_id"], owner)


def list_athletes(owner: str, search: Optional[str] = None) -> List[dict]:
    query = {"created_by": owner}
    if search:
        query["$or"] = [
            {"athlete_id": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}},
        ]
    cursor = athletes_collection.find(query, {"_id": 0}).sort("created_at", -1)
    return list(cursor)


def get_athlete(athlete_id: str, owner: str) -> dict:
    doc = athletes_collection.find_one({"athlete_id": athlete_id, "created_by": owner}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Athlete '{athlete_id}' not found")
    return doc


def update_athlete(athlete_id: str, payload: AthleteUpdate, owner: str) -> dict:
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        return get_athlete(athlete_id, owner)
    updates["updated_at"] = utcnow()
    result = athletes_collection.update_one({"athlete_id": athlete_id, "created_by": owner}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Athlete '{athlete_id}' not found")
    return get_athlete(athlete_id, owner)


def delete_athlete(athlete_id: str, owner: str) -> None:
    result = athletes_collection.delete_one({"athlete_id": athlete_id, "created_by": owner})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Athlete '{athlete_id}' not found")
