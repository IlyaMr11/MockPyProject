from __future__ import annotations

from opsmonitor.models.common import PaginationMeta


def build_pagination(total: int, limit: int, offset: int) -> PaginationMeta:
    next_offset = offset + limit if (offset + limit) < total else None
    return PaginationMeta(
        total=total,
        limit=limit,
        offset=offset,
        has_more=next_offset is not None,
        next_offset=next_offset,
    )
