"""Pydantic response schemas for dataset endpoints (requests use UploadFile, not Pydantic)."""
from typing import List

from pydantic import BaseModel


class DatasetSummary(BaseModel):
    dataset_id: str
    rows: int
    columns: int
