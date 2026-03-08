from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from opsmonitor.models.common import PaginationMeta


class EventSeverity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class EventSource(str, Enum):
    agent = "agent"
    manual = "manual"
    integration = "integration"


class EventCreateRequest(BaseModel):
    device_id: int | None = Field(default=None, ge=1)
    device_external_id: str | None = Field(default=None, min_length=3, max_length=40)
    source: EventSource
    severity: EventSeverity
    message: str = Field(min_length=4, max_length=240)
    payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_device_selector(self) -> "EventCreateRequest":
        if self.device_id is None and self.device_external_id is None:
            raise ValueError("either device_id or device_external_id must be provided")
        return self


class EventResponse(BaseModel):
    id: int
    device_id: int
    device_external_id: str
    source: EventSource
    severity: EventSeverity
    message: str
    payload: dict[str, Any]
    created_at: datetime


class EventListResponse(BaseModel):
    items: list[EventResponse]
    page: PaginationMeta
