from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from opsmonitor.api.dependencies import (
    get_device_service,
    require_read_access,
    require_write_access,
)
from opsmonitor.models.device import (
    DeviceCreateRequest,
    DeviceImportRequest,
    DeviceImportResponse,
    DeviceListResponse,
    DeviceResponse,
    DeviceStatus,
    DeviceSummary,
)
from opsmonitor.services.auth_service import Principal
from opsmonitor.services.device_service import DeviceService


router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=DeviceListResponse)
def list_devices(
    _: Principal = Depends(require_read_access),
    device_service: DeviceService = Depends(get_device_service),
    status_filter: Annotated[DeviceStatus | None, Query(alias="status")] = None,
    site: Annotated[str | None, Query(min_length=3, max_length=32)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DeviceListResponse:
    return device_service.list_devices(
        status=None if status_filter is None else status_filter.value,
        site=site,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(
    payload: DeviceCreateRequest,
    _: Principal = Depends(require_write_access),
    device_service: DeviceService = Depends(get_device_service),
) -> DeviceResponse:
    return device_service.create_device(payload)


@router.post(
    "/import",
    response_model=DeviceImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_devices(
    payload: DeviceImportRequest,
    _: Principal = Depends(require_write_access),
    device_service: DeviceService = Depends(get_device_service),
) -> DeviceImportResponse:
    return device_service.import_devices(payload)


@router.get("/summary", response_model=DeviceSummary)
def get_summary(
    _: Principal = Depends(require_read_access),
    device_service: DeviceService = Depends(get_device_service),
) -> DeviceSummary:
    return device_service.get_summary()
