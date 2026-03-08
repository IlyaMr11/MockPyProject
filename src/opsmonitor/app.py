from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from opsmonitor.api.routes.devices import router as devices_router
from opsmonitor.api.routes.events import router as events_router
from opsmonitor.api.routes.health import router as health_router
from opsmonitor.config import Settings
from opsmonitor.db import Database
from opsmonitor.repositories.device_repository import DeviceRepository
from opsmonitor.repositories.event_repository import EventRepository
from opsmonitor.services.auth_service import AuthService
from opsmonitor.services.device_service import DeviceService
from opsmonitor.services.event_service import EventService
from opsmonitor.services.notification_service import NotificationService
from opsmonitor.utils.cache import TTLCache


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    database = Database(resolved_settings.database_path)
    database.apply_schema()
    if resolved_settings.seed_demo_data:
        database.seed_demo_data()

    device_repository = DeviceRepository(database)
    event_repository = EventRepository(database)
    summary_cache: TTLCache[object] = TTLCache(resolved_settings.cache_ttl_seconds)
    auth_service = AuthService(resolved_settings.api_tokens or {})
    notification_service = NotificationService(
        endpoint=resolved_settings.notification_endpoint,
        timeout_seconds=resolved_settings.notification_timeout_seconds,
    )
    device_service = DeviceService(
        device_repository=device_repository,
        event_repository=event_repository,
        summary_cache=summary_cache,
        critical_event_window_hours=resolved_settings.critical_event_window_hours,
    )
    event_service = EventService(
        device_repository=device_repository,
        event_repository=event_repository,
        notification_service=notification_service,
        summary_cache=summary_cache,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            database.close()

    app = FastAPI(title="OpsMonitor", version="0.1.0", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.database = database
    app.state.auth_service = auth_service
    app.state.device_service = device_service
    app.state.event_service = event_service

    app.include_router(health_router)
    app.include_router(devices_router)
    app.include_router(events_router)

    return app


app = create_app()
