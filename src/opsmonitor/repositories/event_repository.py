from __future__ import annotations

from datetime import datetime, UTC
import json
import sqlite3

from opsmonitor.db import Database
from opsmonitor.models.event import EventCreateRequest


class EventRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def list_events(
        self,
        *,
        device_id: int | None,
        severity: str | None,
        source: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[sqlite3.Row], int]:
        clauses: list[str] = []
        params: list[object] = []

        if device_id is not None:
            clauses.append("e.device_id = ?")
            params.append(device_id)
        if severity:
            clauses.append("e.severity = ?")
            params.append(severity)
        if source:
            clauses.append("e.source = ?")
            params.append(source)

        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        total_row = self._database.fetchone(
            f"""
            SELECT COUNT(*) AS count
            FROM device_events e
            JOIN devices d ON d.id = e.device_id
            {where_clause}
            """,
            params,
        )
        rows = self._database.fetchall(
            f"""
            SELECT
                e.id,
                e.device_id,
                d.external_id AS device_external_id,
                e.source,
                e.severity,
                e.message,
                e.payload_json,
                e.created_at
            FROM device_events e
            JOIN devices d ON d.id = e.device_id
            {where_clause}
            ORDER BY e.id DESC
            LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        )
        total = 0 if total_row is None else int(total_row["count"])
        return rows, total

    def create_event(self, payload: EventCreateRequest, *, device_id: int) -> sqlite3.Row:
        created_at = datetime.now(UTC).isoformat()
        event_id = self._database.execute(
            """
            INSERT INTO device_events (
                device_id,
                source,
                severity,
                message,
                payload_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                device_id,
                payload.source.value,
                payload.severity.value,
                payload.message,
                json.dumps(payload.payload, sort_keys=True),
                created_at,
            ],
        )
        row = self._database.fetchone(
            """
            SELECT
                e.id,
                e.device_id,
                d.external_id AS device_external_id,
                e.source,
                e.severity,
                e.message,
                e.payload_json,
                e.created_at
            FROM device_events e
            JOIN devices d ON d.id = e.device_id
            WHERE e.id = ?
            """,
            [event_id],
        )
        if row is None:
            raise RuntimeError("created event could not be loaded")
        return row

    def count_critical_events_since(self, since: datetime) -> int:
        row = self._database.fetchone(
            """
            SELECT COUNT(*) AS count
            FROM device_events
            WHERE severity = 'critical' AND created_at >= ?
            """,
            [since.isoformat()],
        )
        return 0 if row is None else int(row["count"])
