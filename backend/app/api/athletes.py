"""Athlete management endpoints. Every athlete is scoped to the requesting researcher."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user
from app.schemas.athlete import AthleteCreate, AthleteUpdate
from app.services import athlete_service

router = APIRouter(prefix="/api/athletes", tags=["athletes"])


@router.get("")
def list_athletes(search: Optional[str] = Query(None), user=Depends(get_current_user)):
    return athlete_service.list_athletes(user["username"], search)


@router.post("", status_code=201)
def create_athlete(payload: AthleteCreate, user=Depends(get_current_user)):
    return athlete_service.create_athlete(payload, user["username"])


@router.get("/{athlete_id}")
def get_athlete(athlete_id: str, user=Depends(get_current_user)):
    return athlete_service.get_athlete(athlete_id, user["username"])


@router.put("/{athlete_id}")
def update_athlete(athlete_id: str, payload: AthleteUpdate, user=Depends(get_current_user)):
    return athlete_service.update_athlete(athlete_id, payload, user["username"])


@router.delete("/{athlete_id}", status_code=204)
def delete_athlete(athlete_id: str, user=Depends(get_current_user)):
    athlete_service.delete_athlete(athlete_id, user["username"])
