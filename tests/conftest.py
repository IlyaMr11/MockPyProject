from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from opsmonitor.app import create_app
from opsmonitor.config import Settings, parse_api_tokens


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(
        environment="test",
        database_path=str(tmp_path / "opsmonitor-test.db"),
        cache_ttl_seconds=60,
        critical_event_window_hours=24,
        notification_endpoint="memory://test-notifications",
        notification_timeout_seconds=0.2,
        seed_demo_data=True,
        api_tokens=parse_api_tokens(
            "reader-demo-token:reader:read;"
            "writer-demo-token:writer:read,write;"
            "admin-demo-token:admin:read,write,admin"
        ),
    )


@pytest.fixture()
def app(settings: Settings):
    return create_app(settings)


@pytest.fixture()
def client(app) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def reader_headers() -> dict[str, str]:
    return {"X-Api-Key": "reader-demo-token"}


@pytest.fixture()
def writer_headers() -> dict[str, str]:
    return {"X-Api-Key": "writer-demo-token"}
