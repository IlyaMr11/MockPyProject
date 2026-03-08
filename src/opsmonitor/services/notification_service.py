from __future__ import annotations

import asyncio
import logging

from opsmonitor.models.device import DeviceResponse
from opsmonitor.models.event import EventResponse


class NotificationService:
    def __init__(self, *, endpoint: str, timeout_seconds: float) -> None:
        self._endpoint = endpoint
        self._timeout_seconds = timeout_seconds
        self._logger = logging.getLogger("opsmonitor.notifications")

    async def send_critical_event(
        self,
        *,
        device: DeviceResponse,
        event: EventResponse,
    ) -> None:
        await asyncio.sleep(0)
        self._logger.info(
            "sent critical notification endpoint=%s device=%s severity=%s timeout=%.1f",
            self._endpoint,
            device.external_id,
            event.severity,
            self._timeout_seconds,
        )
