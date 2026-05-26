"""관리자 API 라우터 (Bearer 토큰 인증)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.tech import CrawlLog, ReviewQueue, TechItem, TechStatus
from app.schemas.tech import (
    CrawlLogResponse,
    PaginatedResponse,
    ReviewApproveRequest,
    ReviewQueueItem,
    ReviewRejectRequest,
    TechItemCreate,
    TechItemResponse,
    TechItemUpdate,
)

router = APIRouter(tags=["Admin"], prefix="/admin")

DbDep = Annotated[AsyncSession, Depends(get_db)]


# ─── 인증 의존성 ────────────────────────────────────────────────────────────────

async def verify_admin_token(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Authorization: Bearer <ADMIN_TOKEN> 헤더를 검증한다."""
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization 헤더가 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer 토큰 형식이 아닙니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = parts[1].strip()
    if token != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="유효하지 않은 관리자 토큰입니다.",
        )


AdminAuth = Depends(verify_admin_token)


# ─── GET /api/admin/queue ──────────────────────────────────────────────────────

@router.get(
    "/queue",
    response_model=PaginatedResponse[ReviewQueueItem],
    dependencies=[AdminAuth],
)
async def list_review_queue(
    db: DbDep,
    reviewed: bool | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[ReviewQueueItem]:
    """Deprecated 검토 대기 목록을 반환한다."""
    from sqlalchemy import func

    query = (
        select(ReviewQueue)
        .options(
            selectinload(ReviewQueue.tech_item),
            selectinload(ReviewQueue.suggested_deprecated_by_item),
        )
    )
    if reviewed is not None:
        query = query.where(ReviewQueue.reviewed == reviewed)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total: int = total_result.scalar_one() or 0

    offset = (page - 1) * size
    query = query.order_by(ReviewQueue.detected_at.desc()).offset(offset).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedResponse.create(
        items=[ReviewQueueItem.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
    )


# ─── POST /api/admin/queue/{id}/approve ────────────────────────────────────────

@router.post(
    "/queue/{queue_id}/approve",
    response_model=TechItemResponse,
    dependencies=[AdminAuth],
)
async def approve_deprecated(
    queue_id: uuid.UUID,
    body: ReviewApproveRequest,
    db: DbDep,
) -> TechItemResponse:
    """Deprecated 후보를 승인한다. 해당 TechItem 상태를 deprecated로 변경한다."""
    result = await db.execute(
        select(ReviewQueue)
        .where(ReviewQueue.id == queue_id)
        .options(selectinload(ReviewQueue.tech_item))
    )
    queue_item = result.scalar_one_or_none()

    if queue_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="검토 큐 항목을 찾을 수 없습니다.",
        )
    if queue_item.reviewed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 검토된 항목입니다.",
        )

    # TechItem 상태 변경
    tech_item = queue_item.tech_item
    tech_item.status = TechStatus.deprecated
    tech_item.deprecated_reason = body.reason
    tech_item.deprecated_at = datetime.now(timezone.utc)

    if body.deprecated_by_id is not None:
        # 대체 기술이 존재하는지 확인
        replace_result = await db.execute(
            select(TechItem).where(TechItem.id == body.deprecated_by_id)
        )
        replace_item = replace_result.scalar_one_or_none()
        if replace_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="대체 기술 항목을 찾을 수 없습니다.",
            )
        tech_item.deprecated_by = body.deprecated_by_id

    # 큐 항목 업데이트
    queue_item.reviewed = True
    queue_item.reviewed_at = datetime.now(timezone.utc)
    queue_item.approved = True

    await db.flush()

    # 최신 상태 재조회
    refreshed = await db.execute(
        select(TechItem)
        .where(TechItem.id == tech_item.id)
        .options(selectinload(TechItem.deprecated_by_item))
    )
    updated_item = refreshed.scalar_one()
    return TechItemResponse.model_validate(updated_item)


# ─── POST /api/admin/queue/{id}/reject ────────────────────────────────────────

@router.post(
    "/queue/{queue_id}/reject",
    response_model=dict[str, str],
    dependencies=[AdminAuth],
)
async def reject_deprecated(
    queue_id: uuid.UUID,
    body: ReviewRejectRequest,
    db: DbDep,
) -> dict[str, str]:
    """Deprecated 후보를 거부한다."""
    result = await db.execute(select(ReviewQueue).where(ReviewQueue.id == queue_id))
    queue_item = result.scalar_one_or_none()

    if queue_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="검토 큐 항목을 찾을 수 없습니다.",
        )
    if queue_item.reviewed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 검토된 항목입니다.",
        )

    queue_item.reviewed = True
    queue_item.reviewed_at = datetime.now(timezone.utc)
    queue_item.approved = False
    await db.flush()
    return {"message": "거부 처리되었습니다."}


# ─── POST /api/admin/tech ─────────────────────────────────────────────────────

@router.post(
    "/tech",
    response_model=TechItemResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[AdminAuth],
)
async def create_tech_item(
    body: TechItemCreate,
    db: DbDep,
) -> TechItemResponse:
    """관리자가 기술 항목을 수동으로 추가한다."""
    # source_url 중복 확인
    existing = await db.execute(
        select(TechItem).where(TechItem.source_url == body.source_url)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="동일한 source_url이 이미 존재합니다.",
        )

    item = TechItem(
        id=uuid.uuid4(),
        title=body.title,
        description=body.description,
        summary=body.summary,
        category=body.category,
        status=body.status,
        official_url=body.official_url,
        source_url=body.source_url,
        raw_content=body.raw_content,
        deprecated_by=body.deprecated_by,
        deprecated_reason=body.deprecated_reason,
    )
    db.add(item)
    await db.flush()

    refreshed = await db.execute(
        select(TechItem)
        .where(TechItem.id == item.id)
        .options(selectinload(TechItem.deprecated_by_item))
    )
    created_item = refreshed.scalar_one()
    return TechItemResponse.model_validate(created_item)


# ─── PATCH /api/admin/tech/{id} ────────────────────────────────────────────────

@router.patch(
    "/tech/{item_id}",
    response_model=TechItemResponse,
    dependencies=[AdminAuth],
)
async def update_tech_item(
    item_id: uuid.UUID,
    body: TechItemUpdate,
    db: DbDep,
) -> TechItemResponse:
    """관리자가 기술 항목을 수정한다."""
    result = await db.execute(select(TechItem).where(TechItem.id == item_id))
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기술 항목을 찾을 수 없습니다.",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    item.updated_at = datetime.now(timezone.utc)

    await db.flush()

    refreshed = await db.execute(
        select(TechItem)
        .where(TechItem.id == item_id)
        .options(selectinload(TechItem.deprecated_by_item))
    )
    updated_item = refreshed.scalar_one()
    return TechItemResponse.model_validate(updated_item)


# ─── DELETE /api/admin/tech/{id} ───────────────────────────────────────────────

@router.delete(
    "/tech/{item_id}",
    response_model=dict[str, str],
    dependencies=[AdminAuth],
)
async def delete_tech_item(
    item_id: uuid.UUID,
    db: DbDep,
) -> dict[str, str]:
    """기술 항목을 하드 삭제한다."""
    result = await db.execute(select(TechItem).where(TechItem.id == item_id))
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기술 항목을 찾을 수 없습니다.",
        )

    await db.delete(item)
    await db.flush()
    return {"message": "삭제되었습니다."}


# ─── GET /api/admin/crawl/logs ─────────────────────────────────────────────────

@router.get(
    "/crawl/logs",
    response_model=PaginatedResponse[CrawlLogResponse],
    dependencies=[AdminAuth],
)
async def list_crawl_logs(
    db: DbDep,
    page: int = 1,
    size: int = 20,
) -> PaginatedResponse[CrawlLogResponse]:
    """크롤링 로그 목록을 반환한다."""
    from sqlalchemy import func

    count_result = await db.execute(select(func.count(CrawlLog.id)))
    total = count_result.scalar_one()

    offset = (page - 1) * size
    result = await db.execute(
        select(CrawlLog).order_by(CrawlLog.crawled_at.desc()).offset(offset).limit(size)
    )
    logs = result.scalars().all()

    return PaginatedResponse.create(
        items=[CrawlLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        size=size,
    )


# ─── POST /api/admin/crawl/trigger ─────────────────────────────────────────────

@router.post(
    "/crawl/trigger",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[AdminAuth],
)
async def trigger_crawl() -> dict[str, str]:
    """크롤링을 수동으로 트리거한다 (백그라운드 실행)."""
    import asyncio
    from app.services.crawler import run_crawl_with_log

    # 논블로킹으로 실행
    asyncio.create_task(run_crawl_with_log())
    return {"message": "크롤링이 백그라운드에서 시작되었습니다."}
