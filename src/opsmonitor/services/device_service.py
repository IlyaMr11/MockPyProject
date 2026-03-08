from __future__ import annotations

from datetime import datetime, timedelta, UTC
import json
import sqlite3

from fastapi import HTTPException, status

from opsmonitor.models.device import (
    DeviceCreateRequest,
    DeviceListResponse,
    DeviceResponse,
    DeviceSummary,
)
from opsmonitor.repositories.device_repository import DeviceRepository
from opsmonitor.repositories.event_repository import EventRepository
from opsmonitor.utils.cache import TTLCache
from opsmonitor.utils.pagination import build_pagination


SUMMARY_CACHE_PREFIX = "fleet-summary:v2"


def build_summary_cache_key(site: str | None) -> str:
    return f"{SUMMARY_CACHE_PREFIX}:{site or 'all'}"


class DeviceService:
    def __init__(
        self,
        *,
        device_repository: DeviceRepository,
        event_repository: EventRepository,
        summary_cache: TTLCache[object],
        critical_event_window_hours: int,
    ) -> None:
        self._device_repository = device_repository
        self._event_repository = event_repository
        self._summary_cache = summary_cache
        self._critical_event_window_hours = critical_event_window_hours

    def list_devices(
        self,
        *,
        status: str | None,
        site: str | None,
        limit: int,
        offset: int,
    ) -> DeviceListResponse:
        rows, total = self._device_repository.list_devices(
            status=status,
            site=site,
            limit=limit,
            offset=offset,
        )
        items = [self._device_from_row(row) for row in rows]
        return DeviceListResponse(
            items=items,
            page=build_pagination(total=total, limit=limit, offset=offset),
        )

    def create_device(self, payload: DeviceCreateRequest) -> DeviceResponse:
        existing = self._device_repository.get_device_by_external_id(payload.external_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"device '{payload.external_id}' already exists",
            )
        row = self._device_repository.create_device(payload)
        self._summary_cache.invalidate(build_summary_cache_key(None))
        return self._device_from_row(row)

    def get_summary(self, *, site: str | None = None) -> DeviceSummary:
        cache_key = build_summary_cache_key(site)
        cached = self._summary_cache.get(cache_key)
        if isinstance(cached, DeviceSummary):
            return cached.model_copy(update={"cached": True})

        if site is None:
            counts = self._device_repository.count_by_status()
        else:
            rows, _ = self._device_repository.list_devices(
                status=None,
                site=site,
                limit=500,
                offset=0,
            )
            counts = {"active": 0, "maintenance": 0, "offline": 0}
            for row in rows:
                counts[str(row["status"])] += 1
        since = datetime.now(UTC) - timedelta(hours=self._critical_event_window_hours)
        summary = DeviceSummary(
            total_devices=sum(counts.values()),
            active_devices=counts["active"],
            offline_devices=counts["offline"],
            critical_events_last_day=self._event_repository.count_critical_events_since(
                since
            ),
        )
        self._summary_cache.set(cache_key, summary)
        return summary

    def get_device_by_selector(
        self,
        *,
        device_id: int | None,
        external_id: str | None,
    ) -> DeviceResponse:
        row: sqlite3.Row | None = None
        if device_id is not None:
            row = self._device_repository.get_device_by_id(device_id)
        elif external_id is not None:
            row = self._device_repository.get_device_by_external_id(external_id)

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="device not found",
            )

        return self._device_from_row(row)

    @staticmethod
    def _device_from_row(row: sqlite3.Row) -> DeviceResponse:
        return DeviceResponse(
            id=int(row["id"]),
            external_id=str(row["external_id"]),
            name=str(row["name"]),
            site=str(row["site"]),
            owner_team=str(row["owner_team"]),
            status=str(row["status"]),
            metadata=json.loads(str(row["metadata_json"])),
            last_seen_at=row["last_seen_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
