from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status

from opsmonitor.config import TokenConfig


@dataclass(frozen=True)
class Principal:
    label: str
    scopes: frozenset[str]


class AuthService:
    def __init__(self, token_map: dict[str, TokenConfig]) -> None:
        self._token_map = token_map

    def authenticate(self, api_key: str | None) -> Principal:
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing api key",
            )

        token_config = self._token_map.get(api_key)
        if token_config is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid api key",
            )

        return Principal(
            label=token_config.label,
            scopes=frozenset(token_config.scopes),
        )

    def require_scope(self, principal: Principal, scope: str) -> None:
        if scope not in principal.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"scope '{scope}' is required",
            )
