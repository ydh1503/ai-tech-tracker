from __future__ import annotations

import uuid
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.models.tech import TechCategory, TechStatus

T = TypeVar("T")


# ─── 공통 기반 ─────────────────────────────────────────────────────────────────

class TechItemBase(BaseModel):
    title: str = Field(..., max_length=500, description="기술명")
    description: str | None = Field(None, description="상세 설명")
    category: TechCategory = Field(..., description="카테고리")
    official_url: str | None = Field(None, description="공식 링크")
    source_url: str = Field(..., description="수집 출처 URL")


# ─── 응답 스키마 ───────────────────────────────────────────────────────────────

class DeprecatedByRef(BaseModel):
    """deprecated_by 자기참조 최소 표현 (무한 중첩 방지)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source_url: str
    status: TechStatus


class TechItemResponse(BaseModel):
    """공개 API 상세 응답 — 전체 필드."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    summary: str | None
    category: TechCategory
    status: TechStatus
    official_url: str | None
    source_url: str
    raw_content: str | None
    deprecated_by: uuid.UUID | None
    deprecated_by_item: DeprecatedByRef | None
    deprecated_reason: str | None
    deprecated_at: datetime | None
    tech_released_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TechItemList(BaseModel):
    """공개 API 목록 응답 — 요약 필드."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    summary: str | None
    category: TechCategory
    status: TechStatus
    official_url: str | None
    source_url: str
    deprecated_by: uuid.UUID | None
    deprecated_reason: str | None
    tech_released_at: datetime | None
    created_at: datetime
    updated_at: datetime


# ─── 입력 스키마 ───────────────────────────────────────────────────────────────

class TechItemCreate(BaseModel):
    """관리자 수동 추가."""
    title: str = Field(..., max_length=500)
    description: str | None = None
    summary: str | None = Field(None, max_length=500)
    category: TechCategory
    status: TechStatus = TechStatus.active
    official_url: str | None = None
    source_url: str
    raw_content: str | None = None
    deprecated_by: uuid.UUID | None = None
    deprecated_reason: str | None = None
    tech_released_at: datetime | None = None


class TechItemUpdate(BaseModel):
    """관리자 수정 — 모든 필드 optional."""
    title: str | None = Field(None, max_length=500)
    description: str | None = None
    summary: str | None = Field(None, max_length=500)
    category: TechCategory | None = None
    status: TechStatus | None = None
    official_url: str | None = None
    source_url: str | None = None
    raw_content: str | None = None
    deprecated_by: uuid.UUID | None = None
    deprecated_reason: str | None = None
    deprecated_at: datetime | None = None
    tech_released_at: datetime | None = None


# ─── 검토 큐 스키마 ────────────────────────────────────────────────────────────

class ReviewQueueItem(BaseModel):
    """검토 큐 항목."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tech_item_id: uuid.UUID
    tech_item: TechItemList
    suggested_deprecated_by: uuid.UUID | None
    suggested_deprecated_by_item: DeprecatedByRef | None
    reason: str
    detected_at: datetime
    reviewed: bool
    reviewed_at: datetime | None
    approved: bool | None


class ReviewApproveRequest(BaseModel):
    """Deprecated 승인 요청."""
    deprecated_by_id: uuid.UUID | None = Field(None, description="대체 기술 ID (없어도 됨)")
    reason: str = Field(..., description="Deprecated 사유")


class ReviewRejectRequest(BaseModel):
    """Deprecated 거부 요청."""
    reason: str | None = Field(None, description="거부 사유 (내부 메모용)")


# ─── 크롤링 로그 스키마 ────────────────────────────────────────────────────────

class CrawlLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    crawled_at: datetime
    source: str
    items_found: int
    items_added: int
    items_updated: int
    error: str | None


# ─── 페이지네이션 래퍼 ─────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel, Generic[T]):
    """제네릭 페이지네이션 래퍼."""
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, size: int) -> "PaginatedResponse[T]":
        pages = (total + size - 1) // size if size > 0 else 0
        return cls(items=items, total=total, page=page, size=size, pages=pages)


# ─── 카테고리 통계 ─────────────────────────────────────────────────────────────

class CategoryCount(BaseModel):
    category: TechCategory
    count: int
    active_count: int
    deprecated_count: int


# ─── 타임라인 ──────────────────────────────────────────────────────────────────

class TimelineItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    summary: str | None
    category: TechCategory
    status: TechStatus
    source_url: str
    tech_released_at: datetime | None
    updated_at: datetime
    created_at: datetime
