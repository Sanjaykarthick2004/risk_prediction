"""MongoDB connection and collection access via PyMongo.

Kept intentionally simple for a college project: one client, one database,
plain collection accessors used by the service layer.
"""
import logging

from pymongo import ASCENDING, MongoClient
from pymongo.server_api import ServerApi

from app.config import settings

logger = logging.getLogger(__name__)

client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000, tz_aware=True)
db = client[settings.mongodb_database]

# Collections
users_collection = db["users"]
athletes_collection = db["athletes"]
assessments_collection = db["assessments"]
predictions_collection = db["predictions"]
shap_explanations_collection = db["shap_explanations"]
app_config_collection = db["app_config"]  # small key/value store, e.g. selected training dataset


def check_connection() -> bool:
    """Ping MongoDB to verify connectivity. Returns True if reachable."""
    try:
        client.admin.command("ping")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("MongoDB connectivity check failed: %s", exc)
        return False


def create_indexes():
    """Create basic indexes. Safe to call repeatedly (idempotent)."""
    users_collection.create_index("username", unique=True)
    users_collection.create_index("reset_token")
    athletes_collection.create_index("athlete_id", unique=True)
    assessments_collection.create_index("athlete_id")
    assessments_collection.create_index("assessment_date")
    predictions_collection.create_index("athlete_id")
    predictions_collection.create_index("prediction_date")
    shap_explanations_collection.create_index("prediction_id")
    logger.info("MongoDB indexes ensured.")
