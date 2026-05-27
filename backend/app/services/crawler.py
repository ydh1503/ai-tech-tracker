"""RSS 피드 및 GitHub 릴리즈를 수집하는 크롤러 서비스."""
from __future__ import annotations

import asyncio
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import cache_delete
from app.config import settings
from app.database import AsyncSessionLocal
from app.models.tech import CrawlLog, ReviewQueue, TechItem, TechCategory, TechStatus
from app.services.ai_processor import process_batch, ProcessedItem
from app.utils.deprecated_detector import has_deprecated_signal, extract_deprecated_reason

logger = logging.getLogger(__name__)

# ─── 수집 소스 정의 ─────────────────────────────────────────────────────────────

RSS_SOURCES: list[dict[str, str]] = [
    {"url": "https://news.ycombinator.com/rss", "name": "Hacker News"},
    {"url": "https://feeds.feedburner.com/oreilly/radar/atom", "name": "O'Reilly Radar"},
    {"url": "https://github.blog/feed/", "name": "GitHub Blog"},
    {"url": "https://www.anthropic.com/blog/rss.xml", "name": "Anthropic Blog"},
    {"url": "https://openai.com/blog/rss.xml", "name": "OpenAI Blog"},
    {"url": "https://developers.googleblog.com/feeds/posts/default", "name": "Google Developers Blog"},
]

GITHUB_REPOS: list[str] = [
    "langchain-ai/langchain",
    "microsoft/autogen",
    "crewAIInc/crewAI",
    "Significant-Gravitas/AutoGPT",
    "anthropics/anthropic-sdk-python",
    "anthropics/claude-code",
    "modelcontextprotocol/servers",
    "modelcontextprotocol/python-sdk",
    "modelcontextprotocol/typescript-sdk",
]

GITHUB_API_BASE = "https://api.github.com"


# ─── S6: 소스별 결과 dataclass ─────────────────────────────────────────────────

@dataclass
class SourceResult:
    source_url: str
    source_name: str
    found: int
    added: int
    error: str | None = None


# ─── S3: 상태 추론 헬퍼 ────────────────────────────────────────────────────────

def _infer_status(title: str, tag: str | None) -> TechStatus:
    """제목과 태그에서 초기 TechStatus를 추론한다."""
    combined = f"{title} {tag or ''}".lower()
    if any(k in combined for k in ("alpha", "beta", ".rc", "-rc", "pre-", "preview", "experimental", "dev")):
        return TechStatus.experimental
    return TechStatus.active


# ─── S3: stable 전환 배치 ──────────────────────────────────────────────────────

import re as _re
_VER_RE_STABLE = _re.compile(r'^(.*?)\s+v?(\d+)\.(\d+)\.0\b', _re.IGNORECASE)


async def promote_stable_items() -> int:
    """active 상태이고 patch==0이며 90일 이상된 항목을 stable로 전환한다."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TechItem.id, TechItem.title)
            .where(TechItem.status == TechStatus.active)
            .where(TechItem.created_at < cutoff)
        )
        rows = result.fetchall()
        promote_ids = [
            row[0] for row in rows
            if _VER_RE_STABLE.match(row[1])  # patch==0 판정
        ]
        if promote_ids:
            await db.execute(
                update(TechItem)
                .where(TechItem.id.in_(promote_ids))
                .values(status=TechStatus.stable)
            )
            await db.commit()
            logger.info("stable 전환 완료: %d개 항목", len(promote_ids))
    return len(promote_ids) if promote_ids else 0


# ─── S7: 소프트 중복 감지 헬퍼 ─────────────────────────────────────────────────

async def get_existing_titles(db: AsyncSession) -> set[str]:
    """DB에 이미 존재하는 정규화된 title 집합을 반환한다."""
    result = await db.execute(select(TechItem.title))
    return {re.sub(r"[^a-z0-9\s]", "", row[0].lower()).strip() for row in result.fetchall()}


def _is_soft_duplicate(title: str, existing_normalized: set[str]) -> bool:
    """정규화된 title로 소프트 중복을 감지한다."""
    normalized = re.sub(r"[^a-z0-9\s]", "", title.lower()).strip()
    return normalized in existing_normalized


# ─── RSS 수집 ──────────────────────────────────────────────────────────────────

def _safe_parse_date(date_str: str | None) -> datetime:
    """RSS 날짜 문자열을 datetime으로 변환한다. 실패 시 현재 시각 반환."""
    if not date_str:
        return datetime.now(timezone.utc)
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        return datetime.now(timezone.utc)


async def fetch_rss_items(source: dict[str, str]) -> list[dict[str, object]]:
    """RSS 피드에서 항목을 수집한다."""
    items: list[dict[str, object]] = []
    try:
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, source["url"])
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()

            if not title or not link:
                continue

            # S4: 발행일 파싱
            published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
            tech_released_at = None
            if published_parsed:
                try:
                    tech_released_at = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                except Exception:
                    pass

            items.append(
                {
                    "title": title,
                    "source_url": link,
                    "content": summary,
                    "source_name": source["name"],
                    "tech_released_at": tech_released_at,
                }
            )
        logger.info("RSS [%s]: %d개 항목 수집", source["name"], len(items))
    except Exception as e:
        logger.error("RSS 수집 실패 [%s]: %s", source["name"], e)
    return items


# ─── GitHub 수집 ────────────────────────────────────────────────────────────────

async def fetch_github_releases(
    repo: str, client: httpx.AsyncClient
) -> list[dict[str, object]]:
    """GitHub 릴리즈 이벤트에서 항목을 수집한다."""
    items: list[dict[str, object]] = []
    url = f"{GITHUB_API_BASE}/repos/{repo}/releases?per_page=10"
    headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    for attempt in range(3):
        try:
            response = await client.get(url, headers=headers, timeout=15.0)
            if response.status_code in (403, 429):
                wait = 2 ** attempt
                logger.warning(
                    "GitHub rate limit [%s]: %ds 후 재시도 (%d/3)",
                    repo, wait, attempt + 1,
                )
                await asyncio.sleep(wait)
                continue
            response.raise_for_status()
            releases = response.json()

            for release in releases:
                tag_name: str = release.get("tag_name", "")
                name: str = release.get("name", tag_name)
                body: str = release.get("body", "") or ""
                html_url: str = release.get("html_url", "")

                if not html_url:
                    continue

                # S4: published_at 파싱
                published_at_str = release.get("published_at")
                tech_released_at = None
                if published_at_str:
                    try:
                        tech_released_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                    except ValueError:
                        pass

                items.append(
                    {
                        "title": f"{repo} {name}".strip(),
                        "source_url": html_url,
                        "content": body[:3000],
                        "source_name": f"GitHub/{repo}",
                        "tech_released_at": tech_released_at,
                        "tag": tag_name,
                    }
                )
            logger.info("GitHub [%s]: %d개 릴리즈 수집", repo, len(items))
            break
        except httpx.HTTPStatusError as e:
            logger.error("GitHub API 오류 [%s]: %s", repo, e.response.status_code)
            break
        except Exception as e:
            logger.error("GitHub 수집 실패 [%s]: %s", repo, e)
            break

    return items


# ─── 중복 체크 ──────────────────────────────────────────────────────────────────

async def get_existing_urls(db: AsyncSession) -> set[str]:
    """DB에 이미 존재하는 source_url 집합을 반환한다."""
    result = await db.execute(select(TechItem.source_url))
    return {row[0] for row in result.fetchall()}


# ─── DB 저장 ───────────────────────────────────────────────────────────────────

def _map_category(category_str: str | None) -> TechCategory:
    """AI 응답 카테고리 문자열을 TechCategory Enum으로 변환한다."""
    try:
        if category_str:
            return TechCategory(category_str)
    except ValueError:
        pass
    return TechCategory.skills  # 기본값


async def save_item_and_review(
    db: AsyncSession,
    raw: dict[str, object],
    processed: ProcessedItem,
) -> TechItem:
    """TechItem을 저장하고, deprecated 후보이면 ReviewQueue에 추가한다."""
    item = TechItem(
        id=uuid.uuid4(),
        title=raw["title"],
        description=processed.description,
        summary=processed.summary,
        category=_map_category(processed.category),
        status=_infer_status(str(raw["title"]), raw.get("tag")),
        source_url=raw["source_url"],
        raw_content=raw.get("content", "")[:5000] or None,
        tech_released_at=raw.get("tech_released_at"),
    )
    db.add(item)
    await db.flush()  # id 확보

    # deprecated 후보라면 ReviewQueue에 등록
    is_candidate = processed.is_deprecated_candidate
    if not is_candidate:
        # 휴리스틱 2차 검사
        combined_text = f"{raw['title']} {raw.get('content', '')}"
        is_candidate, _ = has_deprecated_signal(combined_text)

    if is_candidate:
        reason = processed.deprecated_reason or extract_deprecated_reason(
            f"{raw['title']} {raw.get('content', '')}"
        )
        queue_entry = ReviewQueue(
            id=uuid.uuid4(),
            tech_item_id=item.id,
            reason=reason,
            detected_at=datetime.now(timezone.utc),
        )
        db.add(queue_entry)
        logger.info("Deprecated 후보 등록: %s", item.title)

    return item


# ─── 메인 크롤링 함수 ──────────────────────────────────────────────────────────

async def run_crawl() -> dict[str, object]:
    """
    전체 크롤링 파이프라인을 실행한다.

    Returns:
        {"found": N, "added": N, "updated": N, "by_source": {source_name: N}}
    """
    all_raw_items: list[dict[str, object]] = []

    # 1. RSS 수집
    for source in RSS_SOURCES:
        items = await fetch_rss_items(source)
        all_raw_items.extend(items)

    # 2. GitHub 수집
    async with httpx.AsyncClient() as http_client:
        for repo in GITHUB_REPOS:
            items = await fetch_github_releases(repo, http_client)
            all_raw_items.extend(items)

    total_found = len(all_raw_items)
    logger.info("전체 수집: %d개 항목", total_found)

    if not all_raw_items:
        return {"found": 0, "added": 0, "updated": 0, "by_source": {}}

    # 3. 중복 제거 (URL 중복 + 소프트 중복)
    async with AsyncSessionLocal() as db:
        existing_urls = await get_existing_urls(db)
        existing_titles = await get_existing_titles(db)

    new_items = []
    seen_titles: set[str] = set()
    for item in all_raw_items:
        if item["source_url"] in existing_urls:
            continue
        normalized = re.sub(r"[^a-z0-9\s]", "", str(item["title"]).lower()).strip()
        if normalized in existing_titles or normalized in seen_titles:
            logger.info("[SOFT_DUP] 제목 중복 감지, 건너뜀: %s", item["title"])
            continue
        seen_titles.add(normalized)
        new_items.append(item)

    logger.info("신규 항목: %d개 (중복 제거 후)", len(new_items))

    if not new_items:
        return {"found": total_found, "added": 0, "updated": 0, "by_source": {}}

    # 4. AI 처리
    processed_results = await process_batch(new_items)

    # 5. 관련 항목만 DB 저장 (항목별 독립 트랜잭션)
    added = 0
    added_by_source: dict[str, int] = {}
    for raw, processed in zip(new_items, processed_results):
        if not processed.is_relevant:
            continue
        try:
            async with AsyncSessionLocal() as db:
                await save_item_and_review(db, raw, processed)
                await db.commit()
            src = str(raw.get("source_name", "unknown"))
            added_by_source[src] = added_by_source.get(src, 0) + 1
            added += 1
        except Exception as e:
            logger.error("항목 저장 실패 (%s): %s", raw.get("title"), e)

    logger.info("저장 완료: %d개 항목", added)
    return {"found": total_found, "added": added, "updated": 0, "by_source": added_by_source}


async def run_crawl_with_log() -> None:
    """크롤링을 실행하고 CrawlLog에 소스별로 결과를 기록한다."""
    logger.info("크롤링 시작")

    # 전체 실행
    try:
        stats = await run_crawl()
        total_found = stats["found"]
        total_added = stats["added"]
        by_source: dict[str, int] = stats.get("by_source", {})  # type: ignore[assignment]
        error_msg = None
    except Exception as e:
        logger.error("크롤링 전체 실패: %s", e)
        total_found = 0
        total_added = 0
        by_source = {}
        error_msg = str(e)

    # CrawlLog 기록 (소스별 개별 로그)
    async with AsyncSessionLocal() as db:
        if error_msg:
            # 에러 발생 시 단일 로그에 error 기록
            all_sources = (
                [s["url"] for s in RSS_SOURCES]
                + [f"https://github.com/{repo}" for repo in GITHUB_REPOS]
            )
            log = CrawlLog(
                id=uuid.uuid4(),
                source=", ".join(all_sources),
                items_found=total_found,
                items_added=total_added,
                items_updated=0,
                error=error_msg,
            )
            db.add(log)
        else:
            # RSS 소스별 로그
            for source in RSS_SOURCES:
                src_name = source["name"]
                src_added = by_source.get(src_name, 0)
                log = CrawlLog(
                    id=uuid.uuid4(),
                    source=source["url"],
                    items_found=src_added,
                    items_added=src_added,
                    items_updated=0,
                    error=None,
                )
                db.add(log)
            # GitHub 레포별 로그
            for repo in GITHUB_REPOS:
                src_name = f"GitHub/{repo}"
                src_added = by_source.get(src_name, 0)
                log = CrawlLog(
                    id=uuid.uuid4(),
                    source=f"https://github.com/{repo}",
                    items_found=src_added,
                    items_added=src_added,
                    items_updated=0,
                    error=None,
                )
                db.add(log)
        await db.commit()

    # 캐시 무효화
    await cache_delete("categories")
    await cache_delete("timeline")
    logger.info("캐시 무효화 완료: categories, timeline")

    logger.info("크롤링 완료 — 수집: %d, 추가: %d", total_found, total_added)
