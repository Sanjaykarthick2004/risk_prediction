"""Health-check endpoint used by Phase 1 to verify frontend/backend/database wiring."""
from fastapi import APIRouter

from app.database.mongodb import check_connection

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check():
    db_connected = check_connection()
    return {
        "status": "ok",
        "service": "Explainable Injury AI API",
        "database": "connected" if db_connected else "unavailable",
    }
