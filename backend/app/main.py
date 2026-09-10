"""FastAPI application entry point."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    assessments, athletes, auth, dashboard, datasets, evaluation,
    explainability, health, predictions, reports, training,
)
from app.config import settings
from app.core.logging import configure_logging
from app.database.mongodb import create_indexes

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Explainable Injury AI API",
    description="Backend for the Explainable Multimodal AI-Based Athlete Injury Risk Prediction system.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(athletes.router)
app.include_router(assessments.router)
app.include_router(datasets.router)
app.include_router(training.router)
app.include_router(evaluation.router)
app.include_router(predictions.router)
app.include_router(explainability.router)
app.include_router(reports.router)
app.include_router(dashboard.router)


@app.on_event("startup")
def on_startup():
    logger.info("Explainable Injury AI API starting up.")
    try:
        create_indexes()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not create MongoDB indexes at startup: %s", exc)


@app.get("/")
def root():
    return {"message": "Explainable Injury AI API. See /docs for API documentation."}
