from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=not settings.is_production,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """비동기 엔진으로 DB 테이블을 생성하고 FTS 인덱스·트리거를 설정한다."""
    # 모든 모델을 import해야 Base.metadata에 테이블 정보가 등록된다
    from app.models import tech  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # FTS 설정 (idempotent)
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text(
            "ALTER TABLE tech_items ADD COLUMN IF NOT EXISTS search_vector tsvector"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS tech_items_search_gin ON tech_items USING GIN(search_vector)"
        ))
        await conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_search_vector() RETURNS TRIGGER AS $$
            BEGIN
              NEW.search_vector :=
                setweight(to_tsvector('simple', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('simple', COALESCE(NEW.summary, '')), 'B') ||
                setweight(to_tsvector('simple', COALESCE(NEW.description, '')), 'C');
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))
        await conn.execute(text(
            "DROP TRIGGER IF EXISTS tsvector_update ON tech_items"
        ))
        await conn.execute(text("""
            CREATE TRIGGER tsvector_update
              BEFORE INSERT OR UPDATE ON tech_items
              FOR EACH ROW EXECUTE FUNCTION update_search_vector()
        """))
        # 기존 데이터 1회 백필
        await conn.execute(text(
            "UPDATE tech_items SET title = title WHERE search_vector IS NULL"
        ))
