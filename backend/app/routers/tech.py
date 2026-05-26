"""공개 API 라우터."""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Annotated
from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cache import cache_get, cache_set
from app.database import get_db
from app.models.tech import TechCategory, TechItem, TechStatus
from app.schemas.tech import (
    CategoryCount,
    PaginatedResponse,
    TechItemList,
    TechItemResponse,
    TimelineItem,
)

router = APIRouter(tags=["Tech Items"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


# ─── GET /api/tech ─────────────────────────────────────────────────────────────

@router.get("/tech", response_model=PaginatedResponse[TechItemList])
async def list_tech_items(
    db: DbDep,
    category: TechCategory | None = Query(None, description="카테고리 필터"),
    status: TechStatus | None = Query(None, description="상태 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    created_after: datetime | None = Query(None, description="이 날짜 이후 생성된 항목만 반환"),
) -> PaginatedResponse[TechItemList]:
    """기술 항목 목록을 반환한다."""
    query = select(TechItem)

    if category is not None:
        query = query.where(TechItem.category == category)
    if status is not None:
        query = query.where(TechItem.status == status)
    if created_after is not None:
        query = query.filter(TechItem.created_at >= created_after)

    # 전체 수 조회
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # 페이지네이션
    offset = (page - 1) * size
    query = query.order_by(TechItem.updated_at.desc()).offset(offset).limit(size)

    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedResponse.create(
        items=[TechItemList.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
    )


# ─── GET /api/tech/deprecated ──────────────────────────────────────────────────

@router.get("/tech/deprecated", response_model=PaginatedResponse[TechItemResponse])
async def list_deprecated_items(
    db: DbDep,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[TechItemResponse]:
    """Deprecated 항목 목록을 대체 기술 정보와 함께 반환한다."""
    query = (
        select(TechItem)
        .where(TechItem.status == TechStatus.deprecated)
        .options(selectinload(TechItem.deprecated_by_item))
    )

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * size
    query = query.order_by(TechItem.deprecated_at.desc().nullslast()).offset(offset).limit(size)

    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedResponse.create(
        items=[TechItemResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
    )


# ─── GET /api/tech/search ──────────────────────────────────────────────────────

@router.get("/tech/search", response_model=PaginatedResponse[TechItemList])
async def search_tech_items(
    db: DbDep,
    q: str = Query(..., min_length=1, description="검색어"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[TechItemList]:
    """기술명·요약에서 검색한다 (대소문자 무시 부분 일치)."""
    search_term = f"%{q}%"
    query = select(TechItem).where(
        TechItem.title.ilike(search_term)
        | TechItem.summary.ilike(search_term)
        | TechItem.description.ilike(search_term)
        | TechItem.raw_content.ilike(search_term)
    )

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    relevance = case(
        (TechItem.title.ilike(search_term), 0),
        else_=1,
    )
    offset = (page - 1) * size
    query = query.order_by(relevance, TechItem.updated_at.desc()).offset(offset).limit(size)

    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedResponse.create(
        items=[TechItemList.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
    )


# ─── GET /api/tech/{id} ────────────────────────────────────────────────────────

@router.get("/tech/{item_id}", response_model=TechItemResponse)
async def get_tech_item(
    item_id: uuid.UUID,
    db: DbDep,
) -> TechItemResponse:
    """기술 항목 상세 정보를 반환한다."""
    result = await db.execute(
        select(TechItem)
        .where(TechItem.id == item_id)
        .options(selectinload(TechItem.deprecated_by_item))
    )
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기술 항목을 찾을 수 없습니다.",
        )

    return TechItemResponse.model_validate(item)


# ─── GET /api/categories ───────────────────────────────────────────────────────

@router.get("/categories", response_model=list[CategoryCount])
async def list_categories(db: DbDep) -> list[CategoryCount]:
    """카테고리 목록과 각 카테고리의 항목 수를 반환한다."""
    _CACHE_KEY = "categories"

    # 캐시 조회
    cached = await cache_get(_CACHE_KEY)
    if cached is not None:
        return [CategoryCount.model_validate(item) for item in json.loads(cached)]

    # 전체 카테고리별 수
    total_counts_result = await db.execute(
        select(TechItem.category, func.count(TechItem.id).label("count"))
        .group_by(TechItem.category)
    )
    total_map: dict[str, int] = {row[0]: row[1] for row in total_counts_result.fetchall()}

    # active 수
    active_counts_result = await db.execute(
        select(TechItem.category, func.count(TechItem.id).label("count"))
        .where(TechItem.status != TechStatus.deprecated)
        .group_by(TechItem.category)
    )
    active_map: dict[str, int] = {row[0]: row[1] for row in active_counts_result.fetchall()}

    # deprecated 수
    deprecated_counts_result = await db.execute(
        select(TechItem.category, func.count(TechItem.id).label("count"))
        .where(TechItem.status == TechStatus.deprecated)
        .group_by(TechItem.category)
    )
    deprecated_map: dict[str, int] = {
        row[0]: row[1] for row in deprecated_counts_result.fetchall()
    }

    categories = []
    for cat in TechCategory:
        cat_val = cat.value
        total_count = total_map.get(cat_val, 0)
        if total_count == 0:
            continue
        categories.append(
            CategoryCount(
                category=cat,
                count=total_count,
                active_count=active_map.get(cat_val, 0),
                deprecated_count=deprecated_map.get(cat_val, 0),
            )
        )

    result = sorted(categories, key=lambda c: c.count, reverse=True)

    # 캐시 저장 (TTL 300초)
    await cache_set(
        _CACHE_KEY,
        json.dumps([item.model_dump(mode="json") for item in result]),
        ttl=300,
    )

    return result


# ─── GET /api/feed/timeline ────────────────────────────────────────────────────

@router.get("/feed/timeline", response_model=list[TimelineItem])
async def get_timeline(db: DbDep) -> list[TimelineItem]:
    """최근 업데이트된 기술 항목 최대 50개를 반환한다."""
    _CACHE_KEY = "timeline"

    # 캐시 조회
    cached = await cache_get(_CACHE_KEY)
    if cached is not None:
        return [TimelineItem.model_validate(item) for item in json.loads(cached)]

    result = await db.execute(
        select(TechItem).order_by(TechItem.updated_at.desc()).limit(50)
    )
    items = result.scalars().all()
    timeline = [TimelineItem.model_validate(item) for item in items]

    # 캐시 저장 (TTL 300초)
    await cache_set(
        _CACHE_KEY,
        json.dumps([item.model_dump(mode="json") for item in timeline]),
        ttl=300,
    )

    return timeline


# ─── GET /feed.xml ─────────────────────────────────────────────────────────────

@router.get("/feed.xml", response_class=Response)
async def get_atom_feed(db: DbDep) -> Response:
    """최근 20개 항목을 Atom 1.0 XML로 반환한다."""
    from datetime import timezone

    result = await db.execute(
        select(TechItem).order_by(TechItem.updated_at.desc()).limit(20)
    )
    items = result.scalars().all()

    feed = Element("feed")
    feed.set("xmlns", "http://www.w3.org/2005/Atom")

    SubElement(feed, "title").text = "AI 기술 트래커"
    SubElement(feed, "link", href="https://ai-tech-tracker.example.com", rel="alternate")
    SubElement(
        feed,
        "link",
        href="https://ai-tech-tracker.example.com/feed.xml",
        rel="self",
        type="application/atom+xml",
    )
    SubElement(feed, "id").text = "https://ai-tech-tracker.example.com/feed.xml"

    updated_el = SubElement(feed, "updated")
    now_utc = datetime.now(timezone.utc)
    updated_el.text = (items[0].updated_at if items else now_utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    for item in items:
        entry = SubElement(feed, "entry")
        SubElement(entry, "id").text = (
            f"https://ai-tech-tracker.example.com/tech/{item.id}"
        )
        SubElement(entry, "title").text = item.title
        SubElement(
            entry,
            "link",
            href=f"https://ai-tech-tracker.example.com/tech/{item.id}",
            rel="alternate",
        )
        SubElement(entry, "updated").text = item.updated_at.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        SubElement(entry, "published").text = item.created_at.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        if item.summary:
            summary_el = SubElement(entry, "summary")
            summary_el.set("type", "text")
            summary_el.text = item.summary
        if item.description:
            content_el = SubElement(entry, "content")
            content_el.set("type", "text")
            content_el.text = item.description
        cat_val = (
            item.category.value
            if hasattr(item.category, "value")
            else str(item.category)
        )
        SubElement(entry, "category", term=cat_val)

    xml_bytes = tostring(feed, encoding="utf-8", xml_declaration=True)
    return Response(
        content=xml_bytes, media_type="application/atom+xml; charset=utf-8"
    )
