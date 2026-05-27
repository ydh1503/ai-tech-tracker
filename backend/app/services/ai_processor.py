"""Claude API를 사용해 수집된 항목을 분류·요약하는 서비스."""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 10
_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"

_SYSTEM_PROMPT = """당신은 AI 기술 정보 분류 및 한국어 해설 전문가입니다.

이 서비스의 독자 정의:
- Claude Code, ChatGPT, Gemini 같은 AI 도구를 일상에서 사용하는 **한국의 일반 사용자**
- 개발자가 아닌 사람도 있으므로 쉬운 말로 설명해야 함
- 핵심 관심사: "이게 나한테 어떤 도움이 되나? 내 AI 도구를 어떻게 더 잘 쓸 수 있나?"

주어진 텍스트가 "AI를 더 잘 활용하는 방법"과 관련된 기술 정보인지 판단하고,
관련 있다면 지정된 JSON 형식으로 반환하세요.

판단 기준:
- is_relevant: AI 모델 성능 비교/벤치마크는 제외. AI 활용 도구/기법/프레임워크/SDK/업데이트만 포함.
- category 정의:
  * skills: AI 능력 단위, 플러그인, 스킬 확장
  * harness: 실행환경, 프레임워크, 런타임
  * agents: 자율 에이전트 시스템, 에이전트 아키텍처
  * orchestration: 다중 에이전트 조율, 파이프라인 관리
  * integration: 외부 도구 연결 (MCP, API 연동 등)
  * prompting: 프롬프트 기법, 프롬프트 엔지니어링
  * infra: 운영/배포/비용/관측성
  * claude_code: Claude Code CLI의 스킬(skills), 훅(hooks), MCP 서버 연동,
    slash command, settings.json 관련 업데이트. Anthropic의 Claude Code 공식
    발표 및 claude-code CLI 릴리즈 노트. 단, OpenAI/Google/Gemini/GPT 관련
    콘텐츠와 단순 anthropic-sdk-* 버전 업데이트는 claude_code가 아니다.
- SDK/릴리즈 분류 규칙:
  * anthropic-sdk-python / anthropic-sdk-js / anthropic-sdk-* 릴리즈 → integration
  * claude-code CLI 릴리즈 / Claude Code 기능 발표 → claude_code
  * MCP 서버 업데이트(modelcontextprotocol/servers 등) → integration
- is_deprecated_candidate: 텍스트에 "deprecated", "replaced by", "no longer recommended",
  "end of life", "EOL", "superseded", "discontinued", "archived" 등이 포함되면 true.

summary 작성 기준:
- 200자 이내 한국어
- "무엇이 추가·변경됐는지"를 핵심만 담아 간결하게

description 작성 기준 (가장 중요):
- 500자 이내 한국어
- 독자(한국 일반 사용자) 관점에서 "이게 나한테 왜 유용한가, 어떻게 쓸 수 있나"를 설명
- Claude Code, ChatGPT, Gemini 등 실제 AI 도구 사용에 직접 연결되는 활용 팁 포함
- 기술 용어는 괄호로 쉽게 풀어서 설명 (예: "MCP(AI가 외부 도구를 쓸 수 있게 연결해주는 방법)")
- 영어 원문 번역이 아닌, 독자를 위한 **재해석**으로 작성
- is_relevant가 false이면 null

응답은 반드시 아래 JSON만 반환하고, 다른 텍스트는 포함하지 마세요:
{
  "is_relevant": true,
  "category": "skills",
  "summary": "한국어 200자 이내 요약",
  "description": "한국어 500자 이내 활용 설명 — 독자 관점에서 어떻게 쓸 수 있는지 위주로",
  "is_deprecated_candidate": false,
  "deprecated_reason": null
}

분류 예시:
- 제목 "anthropic-sdk-python v0.50.0" → {"is_relevant": true, "category": "integration", ...}
- 제목 "Claude Code v2.1.141 released" → {"is_relevant": true, "category": "claude_code", ...}
- 제목 "OpenAI Codex CLI tool" → {"is_relevant": true, "category": "integration", ...}  // OpenAI 도구는 claude_code가 아님
- 제목 "GPT-4o benchmark comparison" → {"is_relevant": false, ...}  // 벤치마크 비교 제외"""


@dataclass
class ProcessedItem:
    is_relevant: bool
    category: str | None
    summary: str | None
    description: str | None
    is_deprecated_candidate: bool
    deprecated_reason: str | None


def _build_headers(key: str) -> dict[str, str]:
    """API 키 형식에 따라 적절한 인증 헤더를 반환한다."""
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": _ANTHROPIC_VERSION,
    }
    # OAuth 토큰(sk-ant-oat...)은 Bearer, 표준 API 키는 x-api-key
    if key.startswith("sk-ant-oat"):
        headers["Authorization"] = f"Bearer {key}"
    else:
        headers["x-api-key"] = key
    return headers


def _parse_response(content: str) -> ProcessedItem:
    """Claude 응답 JSON을 파싱한다. 파싱 실패 시 is_relevant=False를 반환한다."""
    try:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])

        data = json.loads(cleaned)
        return ProcessedItem(
            is_relevant=bool(data.get("is_relevant", False)),
            category=data.get("category"),
            summary=data.get("summary"),
            description=data.get("description"),
            is_deprecated_candidate=bool(data.get("is_deprecated_candidate", False)),
            deprecated_reason=data.get("deprecated_reason"),
        )
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning("Claude 응답 파싱 실패: %s | 원본: %s", e, content[:200])
        return ProcessedItem(
            is_relevant=False,
            category=None,
            summary=None,
            description=None,
            is_deprecated_candidate=False,
            deprecated_reason=None,
        )


_FAIL_ITEM = ProcessedItem(
    is_relevant=False,
    category=None,
    summary=None,
    description=None,
    is_deprecated_candidate=False,
    deprecated_reason=None,
)


async def process_single_item(
    title: str,
    content: str,
    client: httpx.AsyncClient | None = None,
    headers: dict[str, str] | None = None,
) -> ProcessedItem:
    """단일 항목을 Claude로 처리한다."""
    if headers is None:
        headers = _build_headers(settings.ANTHROPIC_API_KEY)

    user_message = f"제목: {title}\n\n내용:\n{content[:3000]}"
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 512,
        "system": [
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        "messages": [{"role": "user", "content": user_message}],
    }

    try:
        if client is not None:
            response = await client.post(_API_URL, headers=headers, json=payload)
        else:
            async with httpx.AsyncClient(timeout=600) as _client:
                response = await _client.post(_API_URL, headers=headers, json=payload)

        response.raise_for_status()
        data = response.json()
        result_text = data["content"][0]["text"] if data.get("content") else ""
        return _parse_response(result_text)

    except httpx.HTTPStatusError as e:
        logger.error("Anthropic API 오류 (항목: %s): %s %s", title, e, e.response.text[:200])
        return _FAIL_ITEM
    except Exception as e:
        logger.error("처리 오류 (항목: %s): %s", title, e)
        return _FAIL_ITEM


async def process_batch(
    items: list[dict[str, str]],
) -> list[ProcessedItem]:
    """
    항목 목록을 배치로 처리한다.

    Args:
        items: [{"title": "...", "content": "..."}] 형태의 리스트

    Returns:
        ProcessedItem 리스트 (입력 순서와 동일)
    """
    if not items:
        return []

    headers = _build_headers(settings.ANTHROPIC_API_KEY)
    results: list[ProcessedItem] = []

    # 배치 내 연결 재사용
    async with httpx.AsyncClient(timeout=600) as client:
        for batch_start in range(0, len(items), BATCH_SIZE):
            batch = items[batch_start : batch_start + BATCH_SIZE]
            logger.info(
                "AI 배치 처리: %d/%d 항목",
                batch_start + len(batch),
                len(items),
            )

            batch_results = await asyncio.gather(
                *[
                    process_single_item(
                        title=item.get("title", ""),
                        content=item.get("content", ""),
                        client=client,
                        headers=headers,
                    )
                    for item in batch
                ]
            )
            results.extend(batch_results)

    return results
