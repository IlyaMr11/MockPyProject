from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from opsmonitor.api.dependencies import (
    get_event_service,
    require_read_access,
    require_write_access,
)
from opsmonitor.models.event import (
    EventCreateRequest,
    EventListResponse,
    EventResponse,
    EventSeverity,
    EventSource,
)
from opsmonitor.services.auth_service import Principal
from opsmonitor.services.event_service import EventService


router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListResponse)
async def list_events(
    _: Principal = Depends(require_read_access),
    evtSvc: EventService = Depends(get_event_service),
    device_id: Annotated[int | None, Query(ge=1)] = None,
    severity: Annotated[EventSeverity | None, Query()] = None,
    source: Annotated[EventSource | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> EventListResponse:
    sevV = None if severity is None else severity.value
    srcV = None if source is None else source.value
    return await evtSvc.list_events(
        device_id=device_id,
        severity=sevV,
        source=srcV,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreateRequest,
    _: Principal = Depends(require_write_access),
    event_service: EventService = Depends(get_event_service),
) -> EventResponse:
    try:
        return await event_service.create_event(payload)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
