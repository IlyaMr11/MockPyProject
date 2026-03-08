from __future__ import annotations

from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    has_more: bool
    next_offset: int | None = Field(default=None, ge=0)


class ErrorResponse(BaseModel):
    detail: str
