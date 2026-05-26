"""FastAPI 애플리케이션 엔트리포인트."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.routers.admin import router as admin_router
from app.routers.tech import router as tech_router
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.DEBUG if not settings.is_production else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """애플리케이션 시작/종료 이벤트 핸들러."""
    # 시작
    logger.info("애플리케이션 시작 중...")
    await create_tables()
    logger.info("DB 테이블 생성/확인 완료")

    start_scheduler()
    logger.info("스케줄러 시작 완료")

    yield

    # 종료
    stop_scheduler()
    logger.info("스케줄러 종료 완료")
    logger.info("애플리케이션 종료")


app = FastAPI(
    title="AI Tech Tracker",
    description="AI 활용 기술 정보 허브 — 매일 자동 수집·분류·요약",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ─── CORS 미들웨어 ──────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 라우터 등록 ────────────────────────────────────────────────────────────────

app.include_router(tech_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


# ─── 헬스체크 ───────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def health_check() -> dict[str, str]:
    """서버 상태 확인."""
    return {
        "status": "ok",
        "service": "ai-tech-tracker",
        "version": "1.0.0",
        "env": settings.ENV,
    }
