from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_API_TOKENS = (
    "reader-demo-token:reader:read;"
    "writer-demo-token:writer:read,write;"
    "admin-demo-token:admin:read,write,admin"
)


@dataclass(frozen=True)
class TokenConfig:
    label: str
    scopes: tuple[str, ...]


@dataclass(frozen=True)
class Settings:
    environment: str = "local"
    database_path: str = ":memory:"
    cache_ttl_seconds: int = 30
    critical_event_window_hours: int = 24
    notification_endpoint: str = "memory://critical-events"
    notification_timeout_seconds: float = 1.0
    seed_demo_data: bool = True
    api_tokens: dict[str, TokenConfig] | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        raw_tokens = os.getenv("OPS_API_TOKENS", DEFAULT_API_TOKENS)
        return cls(
            environment=os.getenv("OPS_ENVIRONMENT", "local"),
            database_path=os.getenv("OPS_DATABASE_PATH", ":memory:"),
            cache_ttl_seconds=int(os.getenv("OPS_CACHE_TTL_SECONDS", "30")),
            critical_event_window_hours=int(
                os.getenv("OPS_CRITICAL_EVENT_WINDOW_HOURS", "24")
            ),
            notification_endpoint=os.getenv(
                "OPS_NOTIFICATION_ENDPOINT", "memory://critical-events"
            ),
            notification_timeout_seconds=float(
                os.getenv("OPS_NOTIFICATION_TIMEOUT_SECONDS", "1.0")
            ),
            seed_demo_data=os.getenv("OPS_SEED_DEMO_DATA", "1") != "0",
            api_tokens=parse_api_tokens(raw_tokens),
        )


def parse_api_tokens(raw_value: str) -> dict[str, TokenConfig]:
    token_map: dict[str, TokenConfig] = {}
    for chunk in raw_value.split(";"):
        item = chunk.strip()
        if not item:
            continue
        token, label, raw_scopes = item.split(":")
        scopes = tuple(scope.strip() for scope in raw_scopes.split(",") if scope.strip())
        token_map[token] = TokenConfig(label=label, scopes=scopes)
    return token_map
