# DB에 tech_category ENUM이 이미 존재하는 경우:
# psql에서 "ALTER TYPE tech_category ADD VALUE 'claude_code';" 실행 필요
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TechCategory(str, PyEnum):
    skills = "skills"
    harness = "harness"
    agents = "agents"
    orchestration = "orchestration"
    integration = "integration"
    prompting = "prompting"
    infra = "infra"
    claude_code = "claude_code"


class TechStatus(str, PyEnum):
    active = "active"
    stable = "stable"
    deprecated = "deprecated"
    experimental = "experimental"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TechItem(Base):
    __tablename__ = "tech_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[TechCategory] = mapped_column(
        SAEnum(TechCategory, name="tech_category"), nullable=False, index=True
    )
    status: Mapped[TechStatus] = mapped_column(
        SAEnum(TechStatus, name="tech_status"),
        nullable=False,
        default=TechStatus.active,
        index=True,
    )
    official_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True, index=True)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 자기 참조: 이 항목을 대체한 기술
    deprecated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tech_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    deprecated_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    deprecated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 해당 기술 자체의 최초 출시일 (DB 등록일과 별개)
    tech_released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # 관계
    deprecated_by_item: Mapped[TechItem | None] = relationship(
        "TechItem",
        foreign_keys=[deprecated_by],
        remote_side="TechItem.id",
        lazy="selectin",
    )
    review_queues: Mapped[list[ReviewQueue]] = relationship(
        "ReviewQueue",
        foreign_keys="ReviewQueue.tech_item_id",
        back_populates="tech_item",
        lazy="selectin",
    )


class CrawlLog(Base):
    __tablename__ = "crawl_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    source: Mapped[str] = mapped_column(String(2048), nullable=False)
    items_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_added: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class ReviewQueue(Base):
    __tablename__ = "review_queue"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tech_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tech_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    suggested_deprecated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tech_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # 관계
    tech_item: Mapped[TechItem] = relationship(
        "TechItem",
        foreign_keys=[tech_item_id],
        back_populates="review_queues",
        lazy="selectin",
    )
    suggested_deprecated_by_item: Mapped[TechItem | None] = relationship(
        "TechItem",
        foreign_keys=[suggested_deprecated_by],
        lazy="selectin",
    )
