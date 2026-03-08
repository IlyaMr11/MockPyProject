from __future__ import annotations

from datetime import datetime, UTC
import json
import sqlite3

from opsmonitor.db import Database
from opsmonitor.models.device import DeviceCreateRequest


class DeviceRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def list_devices(
        self,
        *,
        status: str | None,
        site: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[sqlite3.Row], int]:
        clauses: list[str] = []
        params: list[object] = []

        if status:
            clauses.append("status = ?")
            params.append(status)
        if site:
            clauses.append("site = ?")
            params.append(site)

        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        total_row = self._database.fetchone(
            f"SELECT COUNT(*) AS count FROM devices {where_clause}",
            params,
        )
        rows = self._database.fetchall(
            f"""
            SELECT
                id,
                external_id,
                name,
                site,
                status,
                owner_team,
                metadata_json,
                last_seen_at,
                created_at,
                updated_at
            FROM devices
            {where_clause}
            ORDER BY id ASC
            LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        )
        total = 0 if total_row is None else int(total_row["count"])
        return rows, total

    def get_device_by_id(self, device_id: int) -> sqlite3.Row | None:
        return self._database.fetchone(
            """
            SELECT
                id,
                external_id,
                name,
                site,
                status,
                owner_team,
                metadata_json,
                last_seen_at,
                created_at,
                updated_at
            FROM devices
            WHERE id = ?
            """,
            [device_id],
        )

    def get_device_by_external_id(self, external_id: str) -> sqlite3.Row | None:
        return self._database.fetchone(
            """
            SELECT
                id,
                external_id,
                name,
                site,
                status,
                owner_team,
                metadata_json,
                last_seen_at,
                created_at,
                updated_at
            FROM devices
            WHERE external_id = ?
            """,
            [external_id],
        )

    def create_device(self, payload: DeviceCreateRequest) -> sqlite3.Row:
        now = datetime.now(UTC).isoformat()
        device_id = self._database.execute(
            """
            INSERT INTO devices (
                external_id,
                name,
                site,
                status,
                owner_team,
                metadata_json,
                last_seen_at,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                payload.external_id,
                payload.name,
                payload.site,
                payload.status.value,
                payload.owner_team,
                json.dumps(payload.metadata, sort_keys=True),
                None,
                now,
                now,
            ],
        )
        row = self.get_device_by_id(device_id)
        if row is None:
            raise RuntimeError("created device could not be loaded")
        return row

    def touch_last_seen(self, device_id: int, seen_at: str) -> None:
        self._database.execute(
            """
            UPDATE devices
            SET last_seen_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [seen_at, seen_at, device_id],
        )

    def count_by_status(self) -> dict[str, int]:
        rows = self._database.fetchall(
            """
            SELECT status, COUNT(*) AS count
            FROM devices
            GROUP BY status
            """
        )
        counts = {"active": 0, "maintenance": 0, "offline": 0}
        for row in rows:
            counts[str(row["status"])] = int(row["count"])
        return counts
