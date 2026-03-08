from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, Request

from opsmonitor.services.auth_service import AuthService, Principal
from opsmonitor.services.device_service import DeviceService
from opsmonitor.services.event_service import EventService


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_device_service(request: Request) -> DeviceService:
    return request.app.state.device_service


def get_event_service(request: Request) -> EventService:
    return request.app.state.event_service


def get_current_principal(
    api_key: Annotated[str | None, Header(alias="X-Api-Key")] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> Principal:
    return auth_service.authenticate(api_key)


def require_read_access(
    principal: Principal = Depends(get_current_principal),
    auth_service: AuthService = Depends(get_auth_service),
) -> Principal:
    auth_service.require_scope(principal, "read")
    return principal


def require_write_access(
    principal: Principal = Depends(get_current_principal),
    auth_service: AuthService = Depends(get_auth_service),
) -> Principal:
    auth_service.require_scope(principal, "write")
    return principal
