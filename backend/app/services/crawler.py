"""RSS 피드 및 GitHub 릴리즈를 수집하는 크롤러 서비스."""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx
from sqlalchemy import select
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


# ─── RSS 수집 ──────────────────────────────────────────────────────────────────

def _safe_parse_date(date_str: str | None) -> datetime:
    """RSS 날짜 문자열을 datetime으로 변환한다. 실패 시 현재 시각 반환."""
    if not date_str:
        return datetime.now(timezone.utc)
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        return datetime.now(timezone.utc)


async def fetch_rss_items(source: dict[str, str]) -> list[dict[str, str]]:
    """RSS 피드에서 항목을 수집한다."""
    items: list[dict[str, str]] = []
    try:
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, source["url"])
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()

            if not title or not link:
                continue

            items.append(
                {
                    "title": title,
                    "source_url": link,
                    "content": summary,
                    "source_name": source["name"],
                }
            )
        logger.info("RSS [%s]: %d개 항목 수집", source["name"], len(items))
    except Exception as e:
        logger.error("RSS 수집 실패 [%s]: %s", source["name"], e)
    return items


# ─── GitHub 수집 ────────────────────────────────────────────────────────────────

async def fetch_github_releases(
    repo: str, client: httpx.AsyncClient
) -> list[dict[str, str]]:
    """GitHub 릴리즈 이벤트에서 항목을 수집한다."""
    items: list[dict[str, str]] = []
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

                items.append(
                    {
                        "title": f"{repo} {name}".strip(),
                        "source_url": html_url,
                        "content": body[:3000],
                        "source_name": f"GitHub/{repo}",
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
    raw: dict[str, str],
    processed: ProcessedItem,
) -> TechItem:
    """TechItem을 저장하고, deprecated 후보이면 ReviewQueue에 추가한다."""
    item = TechItem(
        id=uuid.uuid4(),
        title=raw["title"],
        description=raw.get("content", "")[:1000] or None,
        summary=processed.summary,
        category=_map_category(processed.category),
        status=TechStatus.active,
        source_url=raw["source_url"],
        raw_content=raw.get("content", "")[:5000] or None,
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

async def run_crawl() -> dict[str, int]:
    """
    전체 크롤링 파이프라인을 실행한다.

    Returns:
        {"found": N, "added": N, "updated": N}
    """
    all_raw_items: list[dict[str, str]] = []

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
        return {"found": 0, "added": 0, "updated": 0}

    # 3. 중복 제거
    async with AsyncSessionLocal() as db:
        existing_urls = await get_existing_urls(db)

    new_items = [
        item for item in all_raw_items
        if item["source_url"] not in existing_urls
    ]
    logger.info("신규 항목: %d개 (중복 제거 후)", len(new_items))

    if not new_items:
        return {"found": total_found, "added": 0, "updated": 0}

    # 4. AI 처리
    processed_results = await process_batch(new_items)

    # 5. 관련 항목만 DB 저장 (항목별 독립 트랜잭션)
    added = 0
    for raw, processed in zip(new_items, processed_results):
        if not processed.is_relevant:
            continue
        try:
            async with AsyncSessionLocal() as db:
                await save_item_and_review(db, raw, processed)
                await db.commit()
            added += 1
        except Exception as e:
            logger.error("항목 저장 실패 (%s): %s", raw.get("title"), e)

    logger.info("저장 완료: %d개 항목", added)
    return {"found": total_found, "added": added, "updated": 0}


async def run_crawl_with_log() -> None:
    """크롤링을 실행하고 CrawlLog에 소스별로 결과를 기록한다."""
    logger.info("크롤링 시작")

    # 소스별 로그를 기록하기 위해 소스 목록 정의
    all_sources = (
        [s["url"] for s in RSS_SOURCES]
        + [f"https://github.com/{repo}" for repo in GITHUB_REPOS]
    )

    # 전체 실행
    try:
        stats = await run_crawl()
        total_found = stats["found"]
        total_added = stats["added"]
        error_msg = None
    except Exception as e:
        logger.error("크롤링 전체 실패: %s", e)
        total_found = 0
        total_added = 0
        error_msg = str(e)

    # CrawlLog 기록 (전체를 하나의 로그로)
    async with AsyncSessionLocal() as db:
        log = CrawlLog(
            id=uuid.uuid4(),
            source=", ".join(all_sources),
            items_found=total_found,
            items_added=total_added,
            items_updated=0,
            error=error_msg,
        )
        db.add(log)
        await db.commit()

    # 캐시 무효화
    await cache_delete("categories")
    await cache_delete("timeline")
    logger.info("캐시 무효화 완료: categories, timeline")

    logger.info("크롤링 완료 — 수집: %d, 추가: %d", total_found, total_added)
