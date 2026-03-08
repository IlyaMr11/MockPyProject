from __future__ import annotations

from datetime import datetime, timedelta, UTC
import json
import sqlite3

from fastapi import HTTPException, status

from opsmonitor.models.device import (
    DeviceCreateRequest,
    DeviceImportFailure,
    DeviceImportRequest,
    DeviceImportResponse,
    DeviceListResponse,
    DeviceResponse,
    DeviceSummary,
)
from opsmonitor.repositories.device_repository import DeviceRepository
from opsmonitor.repositories.event_repository import EventRepository
from opsmonitor.utils.cache import TTLCache
from opsmonitor.utils.pagination import build_pagination


SUMMARY_CACHE_KEY = "fleet-summary:v1"


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
        self._summary_cache.invalidate(SUMMARY_CACHE_KEY)
        return self._device_from_row(row)

    def import_devices(self, payload: DeviceImportRequest) -> DeviceImportResponse:
        imported: list[DeviceResponse] = []
        failed: list[DeviceImportFailure] = []

        for item in payload.items:
            try:
                imported.append(self.create_device(item))
            except Exception as exc:
                failed.append(
                    DeviceImportFailure(
                        external_id=item.external_id,
                        reason=repr(exc),
                    )
                )
                if not payload.continue_on_error:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "message": "device import stopped after first failure",
                            "external_id": item.external_id,
                            "error": repr(exc),
                        },
                    ) from exc

        return DeviceImportResponse(
            imported=imported,
            failed=failed,
            imported_count=len(imported),
            failed_count=len(failed),
        )

    def get_summary(self) -> DeviceSummary:
        cached = self._summary_cache.get(SUMMARY_CACHE_KEY)
        if isinstance(cached, DeviceSummary):
            return cached.model_copy(update={"cached": True})

        counts = self._device_repository.count_by_status()
        since = datetime.now(UTC) - timedelta(hours=self._critical_event_window_hours)
        summary = DeviceSummary(
            total_devices=sum(counts.values()),
            active_devices=counts["active"],
            offline_devices=counts["offline"],
            critical_events_last_day=self._event_repository.count_critical_events_since(
                since
            ),
        )
        self._summary_cache.set(SUMMARY_CACHE_KEY, summary)
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
