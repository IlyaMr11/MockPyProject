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

    def _build_log_tags(self, tags: list[str] = []) -> list[str]:
        tags.append(f"endpoint={self._endpoint}")
        return tags

    async def send_critical_event(
        self,
        *,
        device: DeviceResponse,
        event: EventResponse,
    ) -> None:
        await asyncio.sleep(0)
        tags = self._build_log_tags()
        tags.append(f"device={device.external_id}")
        self._logger.info(
            "sent critical notification %s severity=%s timeout=%.1f",
            ",".join(tags),
            event.severity,
            self._timeout_seconds,
        )
