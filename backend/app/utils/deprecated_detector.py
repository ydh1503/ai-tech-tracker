"""deprecated 후보를 텍스트에서 휴리스틱으로 감지하는 유틸리티."""
from __future__ import annotations

import re

# deprecated 신호 키워드 패턴 (대소문자 무시)
_DEPRECATED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bdeprecated\b", re.IGNORECASE),
    re.compile(r"\bno longer (recommended|supported|maintained)\b", re.IGNORECASE),
    re.compile(r"\breplaced by\b", re.IGNORECASE),
    re.compile(r"\bsuperseded by\b", re.IGNORECASE),
    re.compile(r"\bend[- ]of[- ]life\b", re.IGNORECASE),
    re.compile(r"\beol\b", re.IGNORECASE),
    re.compile(r"\blegacy\b", re.IGNORECASE),
    re.compile(r"\bobsolete\b", re.IGNORECASE),
    re.compile(r"\barchived\b", re.IGNORECASE),
    re.compile(r"\bdiscontinued\b", re.IGNORECASE),
    re.compile(r"\bsunsetting\b", re.IGNORECASE),
    re.compile(r"\bsunset\b", re.IGNORECASE),
]


def has_deprecated_signal(text: str) -> tuple[bool, str | None]:
    """
    텍스트에서 deprecated 신호를 감지한다.

    Returns:
        (is_candidate, matched_keyword)
    """
    if not text:
        return False, None

    for pattern in _DEPRECATED_PATTERNS:
        match = pattern.search(text)
        if match:
            return True, match.group(0)

    return False, None


def extract_deprecated_reason(text: str) -> str:
    """
    텍스트에서 deprecated 관련 문장을 추출해 이유로 반환한다.
    감지된 키워드를 포함하는 문장을 최대 2개까지 반환한다.
    """
    is_candidate, keyword = has_deprecated_signal(text)
    if not is_candidate or not keyword:
        return "deprecated 후보로 감지됨"

    sentences = re.split(r"[.!?\n]", text)
    matching: list[str] = []

    for sentence in sentences:
        if re.search(re.escape(keyword), sentence, re.IGNORECASE):
            stripped = sentence.strip()
            if stripped:
                matching.append(stripped)
        if len(matching) >= 2:
            break

    if matching:
        return " / ".join(matching)

    return f"키워드 감지: {keyword}"
