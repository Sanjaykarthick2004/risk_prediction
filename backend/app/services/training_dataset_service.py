"""Tracks which dataset should be used the NEXT time training runs.

This is a single, simple "current selection" pointer stored in MongoDB —
not a dataset registry. The default (no selection) is always the bundled
SYNTHETIC DEMONSTRATION DATA, so the app keeps working immediately after
install with no dataset upload required.
"""
import os

from app.database.mongodb import app_config_collection
from app.utils.helpers import utcnow

_SELECTION_DOC_ID = "training_dataset"

SYNTHETIC_LABEL = "Trained Data"  # UI-facing name for the bundled default dataset


def select_dataset(dataset_id: str, filename: str, path: str) -> dict:
    doc = {
        "_id": _SELECTION_DOC_ID,
        "dataset_id": dataset_id,
        "filename": filename,
        "path": path,
        "selected_at": utcnow(),
    }
    app_config_collection.replace_one({"_id": _SELECTION_DOC_ID}, doc, upsert=True)
    return doc


def clear_selection() -> None:
    app_config_collection.delete_one({"_id": _SELECTION_DOC_ID})


def get_raw_selection() -> dict:
    """Returns the stored selection doc, or None if the file behind it is missing/never selected."""
    doc = app_config_collection.find_one({"_id": _SELECTION_DOC_ID})
    if doc and os.path.exists(doc.get("path", "")):
        return doc
    return None


def get_active_dataset_info() -> dict:
    """What will be used the NEXT time training runs: either an uploaded dataset or the default synthetic one."""
    selected = get_raw_selection()
    if selected:
        return {
            "source": "uploaded",
            "label": selected["filename"],
            "path": selected["path"],
            "dataset_id": selected["dataset_id"],
        }
    return {"source": "synthetic", "label": SYNTHETIC_LABEL, "path": None, "dataset_id": None}
