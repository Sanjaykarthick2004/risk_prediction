"""FastAPI application entry point."""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

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


@app.exception_handler(PyMongoError)
async def mongo_error_handler(request: Request, exc: PyMongoError):
    # An unhandled exception here would otherwise propagate past
    # CORSMiddleware to Starlette's outer error handler, which returns a
    # response with NO Access-Control-Allow-Origin header — the browser then
    # reports a misleading "blocked by CORS policy" error instead of the
    # real problem (the database is unreachable). Registering a handler
    # keeps this inside the middleware stack so CORS headers are still added.
    logger.error("MongoDB error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "The database is temporarily unavailable. Please try again shortly."},
    )


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
