from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from opsmonitor.models.common import PaginationMeta


class DeviceStatus(str, Enum):
    active = "active"
    maintenance = "maintenance"
    offline = "offline"


class DeviceCreateRequest(BaseModel):
    external_id: str = Field(min_length=3, max_length=40, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=3, max_length=80)
    site: str = Field(min_length=3, max_length=32)
    owner_team: str = Field(min_length=3, max_length=40)
    status: DeviceStatus = DeviceStatus.active
    metadata: dict[str, str] = Field(default_factory=dict)


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    name: str
    site: str
    owner_team: str
    status: DeviceStatus
    metadata: dict[str, str]
    last_seen_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class DeviceListResponse(BaseModel):
    items: list[DeviceResponse]
    page: PaginationMeta


class DeviceSummary(BaseModel):
    total_devices: int
    active_devices: int
    offline_devices: int
    critical_events_last_day: int
    cached: bool = False
