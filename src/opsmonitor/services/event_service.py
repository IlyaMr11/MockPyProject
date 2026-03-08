from __future__ import annotations

from datetime import datetime, UTC
import json
import sqlite3

from opsmonitor.models.device import DeviceResponse
from opsmonitor.models.event import EventCreateRequest, EventListResponse, EventResponse
from opsmonitor.repositories.device_repository import DeviceRepository
from opsmonitor.repositories.event_repository import EventRepository
from opsmonitor.services.device_service import SUMMARY_CACHE_KEY
from opsmonitor.services.notification_service import NotificationService
from opsmonitor.utils.cache import TTLCache
from opsmonitor.utils.pagination import build_pagination


class EventService:
    def __init__(
        self,
        *,
        device_repository: DeviceRepository,
        event_repository: EventRepository,
        notification_service: NotificationService,
        summary_cache: TTLCache[object],
    ) -> None:
        self._device_repository = device_repository
        self._event_repository = event_repository
        self._notification_service = notification_service
        self._summary_cache = summary_cache

    async def list_events(
        self,
        *,
        device_id: int | None,
        severity: str | None,
        source: str | None,
        limit: int,
        offset: int,
    ) -> EventListResponse:
        rows, total = self._event_repository.list_events(
            device_id=device_id,
            severity=severity,
            source=source,
            limit=limit,
            offset=offset,
        )
        items = [self._event_from_row(row) for row in rows]
        return EventListResponse(
            items=items,
            page=build_pagination(total=total, limit=limit, offset=offset),
        )

    async def create_event(self, payload: EventCreateRequest) -> EventResponse:
        device_row = self._resolve_device_row(payload)
        event_row = self._event_repository.create_event(
            payload,
            device_id=int(device_row["id"]),
        )
        timestamp = datetime.now(UTC).isoformat()
        self._device_repository.touch_last_seen(int(device_row["id"]), timestamp)
        self._summary_cache.invalidate(SUMMARY_CACHE_KEY)

        event = self._event_from_row(event_row)
        if event.severity == "critical":
            self._notification_service.send_critical_event(
                device=self._device_from_row(device_row),
                event=event,
            )
        return event

    def _resolve_device_row(self, payload: EventCreateRequest) -> sqlite3.Row:
        row: sqlite3.Row | None = None
        if payload.device_id is not None:
            row = self._device_repository.get_device_by_id(payload.device_id)
        elif payload.device_external_id is not None:
            row = self._device_repository.get_device_by_external_id(
                payload.device_external_id
            )

        if row is None:
            raise LookupError("device not found")
        return row

    @staticmethod
    def _event_from_row(row: sqlite3.Row) -> EventResponse:
        return EventResponse(
            id=int(row["id"]),
            device_id=int(row["device_id"]),
            device_external_id=str(row["device_external_id"]),
            source=str(row["source"]),
            severity=str(row["severity"]),
            message=str(row["message"]),
            payload=json.loads(str(row["payload_json"])),
            created_at=row["created_at"],
        )

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
