from __future__ import annotations

from datetime import datetime, timedelta, UTC
import sqlite3
from typing import Any, Iterable


SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    site TEXT NOT NULL,
    status TEXT NOT NULL,
    owner_team TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    last_seen_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
CREATE INDEX IF NOT EXISTS idx_devices_site ON devices(site);

CREATE TABLE IF NOT EXISTS device_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    source TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY(device_id) REFERENCES devices(id)
);

CREATE INDEX IF NOT EXISTS idx_device_events_device_id ON device_events(device_id);
CREATE INDEX IF NOT EXISTS idx_device_events_severity ON device_events(severity);
CREATE INDEX IF NOT EXISTS idx_device_events_created_at ON device_events(created_at);
"""


class Database:
    def __init__(self, path: str) -> None:
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")

    def apply_schema(self) -> None:
        self._connection.executescript(SCHEMA)
        self._connection.commit()

    def fetchall(
        self, query: str, params: Iterable[Any] | None = None
    ) -> list[sqlite3.Row]:
        cursor = self._connection.execute(query, tuple(params or ()))
        return list(cursor.fetchall())

    def fetchone(
        self, query: str, params: Iterable[Any] | None = None
    ) -> sqlite3.Row | None:
        cursor = self._connection.execute(query, tuple(params or ()))
        return cursor.fetchone()

    def execute(self, query: str, params: Iterable[Any] | None = None) -> int:
        cursor = self._connection.execute(query, tuple(params or ()))
        self._connection.commit()
        return int(cursor.lastrowid)

    def executemany(self, query: str, rows: Iterable[Iterable[Any]]) -> None:
        self._connection.executemany(query, rows)
        self._connection.commit()

    def seed_demo_data(self) -> None:
        existing = self.fetchone("SELECT COUNT(*) AS count FROM devices")
        if existing is None or int(existing["count"]) > 0:
            return

        now = datetime.now(UTC)
        devices = [
            (
                "edge-gw-1",
                "Edge Gateway 1",
                "fra-1",
                "active",
                "ops-core",
                '{"rack":"r1"}',
                (now - timedelta(minutes=8)).isoformat(),
                (now - timedelta(days=20)).isoformat(),
                (now - timedelta(minutes=8)).isoformat(),
            ),
            (
                "sensor-hub-2",
                "Sensor Hub 2",
                "fra-1",
                "maintenance",
                "field-ops",
                '{"rack":"r2"}',
                (now - timedelta(hours=5)).isoformat(),
                (now - timedelta(days=12)).isoformat(),
                (now - timedelta(hours=5)).isoformat(),
            ),
            (
                "cooling-node-3",
                "Cooling Node 3",
                "iad-2",
                "offline",
                "infra-west",
                '{"rack":"b4"}',
                None,
                (now - timedelta(days=5)).isoformat(),
                (now - timedelta(days=1)).isoformat(),
            ),
        ]
        self.executemany(
            """
            INSERT INTO devices (
                external_id, name, site, status, owner_team, metadata_json,
                last_seen_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            devices,
        )

        events = [
            (
                1,
                "agent",
                "info",
                "heartbeat restored",
                '{"latency_ms":42}',
                (now - timedelta(hours=3)).isoformat(),
            ),
            (
                1,
                "integration",
                "critical",
                "temperature threshold breached",
                '{"temperature_c":91}',
                (now - timedelta(hours=2)).isoformat(),
            ),
            (
                2,
                "manual",
                "warning",
                "maintenance window extended",
                '{"ticket":"OPS-204"}',
                (now - timedelta(hours=12)).isoformat(),
            ),
        ]
        self.executemany(
            """
            INSERT INTO device_events (
                device_id, source, severity, message, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            events,
        )

    def close(self) -> None:
        self._connection.close()
