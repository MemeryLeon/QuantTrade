from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DataSnapshot:
    id: str
    source_id: str
    market: str
    instrument_scope: str
    resolution: str
    adjustment: str
    start_time: datetime
    end_time: datetime
    timezone: str
    calendar_version: str
    schema_version: str
    object_uri: str
    checksum: str
    row_count: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AdjustmentFactor:
    effective_date: datetime
    factor: str


@dataclass(frozen=True, slots=True)
class CompanyAction:
    effective_date: datetime
    action_type: str
    description: str

