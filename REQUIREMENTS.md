# AI 기술 트래커 — 기능 현황 및 백로그

**최종 업데이트**: 2026-05-27

---

## 현재 구현 상태

### 백엔드 (FastAPI)

| 기능 | 파일 | 상태 |
|------|------|------|
| TechItem / CrawlLog / ReviewQueue 모델 | `models/tech.py` | 완료 |
| 공개 API (목록, 상세, 검색, deprecated, 카테고리, 타임라인) | `routers/tech.py` | 완료 |
| 관리자 API (deprecated 승인/거부, 수동 추가/수정/삭제, 크롤 트리거/로그) | `routers/admin.py` | 완료 |
| RSS 수집 (HN, O'Reilly, GitHub Blog) | `services/crawler.py` | 완료 |
| GitHub 릴리즈 수집 (LangChain, AutoGPT, CrewAI, AutoGen, anthropic-sdk-python) | `services/crawler.py` | 완료 |
| Claude AI 분류·요약·deprecated 후보 감지 (배치 + 프롬프트 캐싱) | `services/ai_processor.py` | 완료 |
| 휴리스틱 deprecated 키워드 감지 | `utils/deprecated_detector.py` | 완료 |
| APScheduler 크론 (매일 18:00 UTC = KST 03:00) | `services/scheduler.py` | 완료 |
| Redis 캐시 (categories, timeline TTL 300초) | `cache.py` | 완료 |
| DB 자동 테이블 생성 (`create_tables()`) | `database.py` | 완료 |

### 프론트엔드 (Next.js 15)

| 기능 | 파일 | 상태 |
|------|------|------|
| 메인 피드 | `app/page.tsx` | 완료 |
| 카테고리별 목록 | `app/category/[slug]/page.tsx` | 완료 |
| 기술 상세 페이지 | `app/tech/[id]/page.tsx` | 완료 |
| Deprecated 목록 | `app/deprecated/page.tsx` | 완료 |
| 검색 결과 | `app/search/page.tsx` | 완료 |
| 관리자 페이지 | `app/admin/page.tsx` | 완료 |
| TechCard / StatusBadge / DeprecatedBanner | `components/` | 완료 |
| SearchBar / CategoryNav / Timeline | `components/` | 완료 |
| 카테고리 설명 헤더 | `app/category/[slug]/page.tsx`, `components/CategoryNav.tsx` | 완료 |
| 페이지네이션 UI | `components/Pagination.tsx`, 각 목록 페이지 | 완료 |

---

## 알려진 이슈

> 2026-05-27 Opus 평가 에이전트 검토 결과를 반영하여 갱신.

| # | 이슈 | 영향도 | 위치 |
|---|------|--------|------|
| 1 | **스케줄러 비동기 충돌** — `BackgroundScheduler`(동기) + `asyncio.run()` 패턴이 FastAPI 메인 이벤트 루프와 충돌하여 예약 크롤링이 실제로 실행되지 않을 가능성 높음. 수집 데이터가 5/26 하루치뿐인 정황 근거. | **치명** | `services/scheduler.py:21,34` |
| 2 | **AI 분류 일관성 없음** — 동일 SDK(`anthropic-sdk-python`)의 연속 릴리즈가 `harness`, `orchestration`, `integration`, `harness` 4개 카테고리로 흩어짐. OpenAI Codex 글이 `claude_code`로 오분류. | **높음** | `services/ai_processor.py` 시스템 프롬프트 |
| 3 | **크롤러 실행 후 Redis 캐시 무효화 없음** — 신규 항목 추가·admin 수정 후 최대 5분간 구버전 데이터 반환 | 중간 | `services/crawler.py` 끝, `routers/admin.py` |
| 4 | **GitHub RSS 동기 블로킹** — `feedparser.parse()`가 async 함수 내 동기 호출로 6개 피드 순차 실행 중 이벤트 루프 블로킹 | 중간 | `services/crawler.py:64` |
| 5 | **GitHub rate limit 미처리** — 403 오류를 `logger.error`로만 처리, 재시도·백오프 없음. 토큰 없이 9개 레포 호출 시 60req/h 한도 초과 가능 | 중간 | `services/crawler.py:122` |
| 6 | **홈/타임라인 중복 노출** — 메인 피드의 `LatestTechList`(최근 20개)와 `RecentTimeline`(최근 15개) 모두 `updated_at` 역순으로 같은 데이터를 두 번 표시 | 낮음 | `app/page.tsx:80,238` |
| 7 | **Alembic 마이그레이션 미적용** — 스키마 변경 시 수동 ALTER TABLE 필요. 운영 환경 위험 | 높음 | `database.py` |
| 8 | **검색 관련도 정렬 없음** — `ILIKE` 부분일치 + `updated_at` 역순. `raw_content`/`description` 본문 검색 제외 | 낮음 | `routers/tech.py:114-124` |
| 9 | **stable/experimental 상태 미사용** — 크롤러가 항상 `active`만 저장. `TechStatus` 4개 상태 중 2개 잉여 | 낮음 | `services/crawler.py:161`, `models/tech.py:28-32` |
| 10 | `CategoryCount` 타입이 `count`만 노출 — `active_count`, `deprecated_count` 미사용 | 낮음 | `frontend/src/lib/types.ts` |

---

## 스프린트 1 ✅ 완료 (2026-05-26 ~ 2026-05-27)

아래 세 기능을 구현 완료했다.

---

### [FEAT-1] Claude Code 전용 수집 소스 및 카테고리 추가

**목적**: 현재 트래커는 일반 AI 생태계 정보만 수집한다. Claude Code CLI 사용에 직접 도움이 되는
Anthropic 공식 발표, MCP 서버 업데이트, claude-code 릴리즈를 자동 수집하도록 보강한다.

#### 백엔드 변경

**파일 1: `backend/app/services/crawler.py`**

`RSS_SOURCES` 리스트에 아래 항목 추가:
```python
{"url": "https://www.anthropic.com/blog/rss.xml", "name": "Anthropic Blog"},
{"url": "https://openai.com/blog/rss.xml", "name": "OpenAI Blog"},
{"url": "https://developers.googleblog.com/feeds/posts/default", "name": "Google Developers Blog"},
```

`GITHUB_REPOS` 리스트에 아래 항목 추가:
```python
"anthropics/claude-code",               # Claude Code CLI 릴리즈
"modelcontextprotocol/servers",         # 공식 MCP 서버 모음
"modelcontextprotocol/python-sdk",      # MCP Python SDK
"modelcontextprotocol/typescript-sdk",  # MCP TypeScript SDK
```

`per_page` 값을 5 → 10으로 변경 (crawler.py:87):
```python
url = f"{GITHUB_API_BASE}/repos/{repo}/releases?per_page=10"
```

**파일 2: `backend/app/models/tech.py`**

`TechCategory` Enum에 `claude_code` 추가:
```python
class TechCategory(str, PyEnum):
    skills = "skills"
    harness = "harness"
    agents = "agents"
    orchestration = "orchestration"
    integration = "integration"
    prompting = "prompting"
    infra = "infra"
    claude_code = "claude_code"   # 추가
```

**파일 3: `backend/app/services/ai_processor.py`**

시스템 프롬프트 `_SYSTEM_PROMPT`의 `category 정의` 섹션에 `claude_code` 설명 추가:
```
* claude_code: Claude Code CLI의 스킬(skills), 훅(hooks), MCP 서버 연동,
  slash command, 설정(settings.json) 관련 업데이트. Anthropic의 Claude Code
  공식 발표 포함. claude-code GitHub 릴리즈 노트도 이 카테고리로 분류.
```

#### 프론트엔드 변경

**파일 4: `frontend/src/lib/types.ts`**

`Category` 타입에 `claude_code` 추가:
```typescript
export type Category =
  | "skills"
  | "harness"
  | "agents"
  | "orchestration"
  | "integration"
  | "prompting"
  | "infra"
  | "claude_code";   // 추가
```

`CATEGORY_LABELS`에 한국어 레이블 추가:
```typescript
export const CATEGORY_LABELS: Record<Category, string> = {
  ...기존...,
  claude_code: "Claude Code",
};
```

#### 완료 조건
- [x] `/api/categories` 응답에 `claude_code` 카테고리가 포함된다
- [x] `/category/claude_code` 페이지가 오류 없이 렌더링된다
- [x] 크롤링 수동 트리거 후 Anthropic Blog / MCP 관련 항목이 수집된다

---

### [FEAT-2] 카테고리 설명 헤더

**목적**: 카테고리 페이지(`/category/[slug]`)에 진입하거나 카테고리 탭을 눌렀을 때,
해당 카테고리가 무엇인지 설명하는 헤더를 표시한다.
처음 방문하는 사용자가 "Skills가 뭔지", "Harness가 뭔지" 바로 알 수 있게 한다.

#### 설명 내용 정의

아래 내용을 코드에 상수로 정의한다 (`frontend/src/lib/types.ts`에 추가):

```typescript
export interface CategoryMeta {
  label: string;       // 한국어 표시명
  description: string; // 1~2문장 설명
  examples: string[];  // 대표 예시 3~5개
}

export const CATEGORY_META: Record<Category, CategoryMeta> = {
  skills: {
    label: "스킬",
    description:
      "AI가 수행할 수 있는 능력 단위. 특정 작업을 처리하는 플러그인이나 도구 형태로, AI의 기능을 목적별로 확장한다.",
    examples: ["Code Review Skill", "PDF Skill", "PPTX Skill", "Web Search Skill"],
  },
  harness: {
    label: "하네스",
    description:
      "AI를 특정 워크플로에 실행하고 통제하는 프레임워크·실행환경. 에이전트가 동작하는 규칙과 컨텍스트를 정의한다.",
    examples: ["Claude Code Harness", "LangChain", "LlamaIndex"],
  },
  agents: {
    label: "에이전트",
    description:
      "자율적으로 태스크를 계획하고 실행하는 AI 시스템. 사람의 개입 없이 다단계 작업을 처리하며, 필요 시 도구를 호출한다.",
    examples: ["Claude Agent SDK", "AutoGPT", "CrewAI", "Devin"],
  },
  orchestration: {
    label: "오케스트레이션",
    description:
      "여러 AI 에이전트나 파이프라인을 조율하는 방법. 각 에이전트의 역할을 분담하고 결과를 통합한다.",
    examples: ["Multi-agent", "AutoGen", "Swarm", "CrewAI Flows"],
  },
  integration: {
    label: "인테그레이션",
    description:
      "AI와 외부 도구·서비스·데이터를 연결하는 방법. 표준 프로토콜 또는 커스텀 API로 AI의 접근 범위를 확장한다.",
    examples: ["MCP (Model Context Protocol)", "Tool Use", "RAG", "Function Calling"],
  },
  prompting: {
    label: "프롬프팅",
    description:
      "AI에서 더 나은 결과를 얻기 위한 입력 설계 기법. 모델 동작을 유도하는 패턴과 전략을 다룬다.",
    examples: ["Chain of Thought", "ReAct", "Few-shot", "Prompt Caching", "System Prompts"],
  },
  infra: {
    label: "인프라 / 운영",
    description:
      "AI 시스템의 배포·운영·비용·품질 관리. 프로덕션 환경에서 AI를 안정적으로 운영하기 위한 기반 기술.",
    examples: ["토큰 최적화", "비용 모니터링", "LLMOps", "관측성(Observability)"],
  },
  claude_code: {
    label: "Claude Code",
    description:
      "Anthropic의 Claude Code CLI 관련 공식 업데이트. 스킬·훅·MCP 서버 연동·설정·slash command 등 Claude Code를 더 잘 활용하기 위한 정보.",
    examples: ["새 스킬 릴리즈", "MCP 서버 업데이트", "hooks 설정", "settings.json 변경", "slash command 추가"],
  },
};
```

#### 프론트엔드 변경

**파일 1: `frontend/src/lib/types.ts`**
- `CategoryMeta` 인터페이스 추가
- `CATEGORY_META` 상수 추가 (위 내용)

**파일 2: `frontend/src/app/category/[slug]/page.tsx`**

카드 목록 위에 설명 헤더 섹션 추가:

```
┌─────────────────────────────────────────────────┐
│  [카테고리 아이콘]  에이전트                          │
│                                                 │
│  자율적으로 태스크를 계획하고 실행하는 AI 시스템.         │
│  사람의 개입 없이 다단계 작업을 처리하며,               │
│  필요 시 도구를 호출한다.                            │
│                                                 │
│  예시:  Claude Agent SDK  AutoGPT  CrewAI  Devin │
└─────────────────────────────────────────────────┘
   [카드] [카드] [카드] ...
```

- `CATEGORY_META[slug]`에서 데이터를 가져와 렌더링
- 존재하지 않는 slug이면 404 반환 (기존 동작 유지)
- 예시 항목은 회색 pill/badge 형태로 나열

**파일 3: `frontend/src/components/CategoryNav.tsx`**

카테고리 탭 네비게이션에서 현재 선택된 카테고리 탭에 툴팁 또는 서브텍스트로 설명 1줄 표시.
모바일에서는 툴팁 숨김 처리.

#### 완료 조건
- [x] `/category/agents` 접근 시 페이지 상단에 설명 헤더가 표시된다
- [x] `/category/claude_code` 에서도 설명이 표시된다
- [x] 존재하지 않는 slug(`/category/unknown`)은 404를 반환한다
- [x] 설명 헤더의 예시 항목이 pill 형태로 나열된다

---

### [FEAT-3] 페이지네이션 UI

**목적**: 현재 모든 목록 페이지가 첫 페이지 데이터만 표시하며 더 많은 항목을 볼 방법이 없다.
URL 쿼리 파라미터(`?page=N`) 기반 페이지네이션을 추가하여 전체 데이터를 탐색 가능하게 한다.

**URL 파라미터 방식 채택 이유**: 서버 컴포넌트 호환, 뒤로가기/북마크 지원, SEO 유리.

#### 적용 대상 페이지

| 페이지 | 파일 | URL 예시 |
|--------|------|---------|
| 메인 피드 | `app/page.tsx` | `/?page=2` |
| 카테고리 | `app/category/[slug]/page.tsx` | `/category/agents?page=3` |
| 검색 결과 | `app/search/page.tsx` | `/search?q=mcp&page=2` |

#### 신규 컴포넌트 명세

**파일: `frontend/src/components/Pagination.tsx`**

```
props:
  currentPage: number   — 현재 페이지 (1-based)
  totalPages:  number   — 전체 페이지 수
  basePath:    string   — 페이지 번호 없는 기본 경로 (예: "/category/agents")
  searchParams?: Record<string, string>  — 유지할 기존 쿼리 파라미터 (예: {q: "mcp"})
```

UI 구조:
```
[← 이전]  [1]  [2]  [3]  ...  [N]  [다음 →]
              ^^^현재 페이지 강조
```

- 현재 페이지 ±2 범위의 번호만 표시 (최대 5개), 범위 밖은 `...`으로 생략
- 첫 페이지/마지막 페이지는 항상 표시
- 현재 페이지가 첫 페이지이면 "← 이전" 비활성화 (렌더링은 하되 클릭 불가)
- 현재 페이지가 마지막 페이지이면 "다음 →" 비활성화
- 전체 페이지가 1페이지이면 컴포넌트 렌더링 안 함 (null 반환)
- `<Link href=...>` 사용 (클라이언트 상태 없음, 서버 컴포넌트에서 사용 가능)

페이지 URL 생성 규칙:
- 1페이지는 `?page=` 파라미터 생략 (예: `/category/agents` — 클린 URL)
- 2페이지 이상은 `?page=N` 추가
- 기존 쿼리 파라미터 유지 (예: `/search?q=mcp&page=2`)

#### 각 페이지 변경 사항

**`app/page.tsx` (메인 피드)**
- `searchParams`에서 `page` 파라미터 읽기 (기본값 1)
- `fetchTechList({ page, size: 20 })` 호출
- 카드 목록 아래 `<Pagination>` 컴포넌트 렌더링

**`app/category/[slug]/page.tsx`**
- `searchParams`에서 `page` 파라미터 읽기
- `fetchTechList({ category: slug, page, size: 20 })` 호출
- 설명 헤더(FEAT-2) 아래 카드 목록, 그 아래 `<Pagination>` 렌더링

**`app/search/page.tsx`**
- `searchParams`에서 `page` 파라미터 읽기
- `searchTech(q, page)` 호출
- `<Pagination searchParams={{ q }}>` 형태로 q 파라미터 유지

#### 완료 조건
- [x] 메인 피드(`/`)에서 `?page=2`로 이동 시 다음 20개 항목이 표시된다
- [x] 카테고리 페이지에서 페이지 번호 클릭이 동작한다
- [x] 검색 결과에서 페이지 이동 시 검색어(`q=`)가 유지된다
- [x] 총 1페이지 분량이면 페이지네이션 컴포넌트가 표시되지 않는다
- [x] "← 이전"/"다음 →" 버튼이 첫/마지막 페이지에서 비활성화된다
- [x] 뒤로가기 후 이전 페이지로 정확히 복귀한다

---

## 스프린트 1 작업 분배 ✅ 완료

| Agent | 담당 기능 | 주요 변경 파일 |
|-------|---------|-------------|
| Agent-A | FEAT-1: Claude Code 소스 + 카테고리 | `crawler.py`, `models/tech.py`, `ai_processor.py`, `types.ts` |
| Agent-B | FEAT-2: 카테고리 설명 헤더 | `types.ts`, `app/category/[slug]/page.tsx`, `components/CategoryNav.tsx` |
| Agent-C | FEAT-3: 페이지네이션 UI | `components/Pagination.tsx` (신규), `app/page.tsx`, `app/category/[slug]/page.tsx`, `app/search/page.tsx` |

---

## 스프린트 2 (다음 개발 대상)

> 2026-05-27 Opus 평가 에이전트 결과를 바탕으로 도출한 긴급 수정 항목.
> 스케줄러 충돌(치명)과 AI 분류 오류(높음)를 우선 처리한다.

---

### [FIX-1] 스케줄러 비동기 충돌 해결 ⚡ 치명

**문제**: `APScheduler.BackgroundScheduler`(동기) 내에서 `asyncio.run()`을 호출하는 현재 구조는
FastAPI 메인 이벤트 루프와 충돌한다. 예약 크롤링이 실제로 실행되지 않거나 예외 없이 실패할 수 있다.
수집 데이터가 수동 트리거 분량뿐인 것이 주요 근거.

**변경 파일**: `backend/app/services/scheduler.py`

**해결 방법**:
```python
# Before (문제 있는 패턴)
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: asyncio.run(run_crawl_with_log()), "cron", hour=18)

# After (권장 패턴)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(run_crawl_with_log, "cron", hour=18)
```

- `AsyncIOScheduler`를 사용하면 FastAPI의 기존 이벤트 루프 안에서 코루틴을 직접 스케줄링
- `lifespan` 컨텍스트에서 `scheduler.start()` / `scheduler.shutdown()` 호출로 라이프사이클 연동
- `asyncio.run()` 호출 완전 제거

**완료 조건**:
- [ ] 서버 재시작 후 다음 크롤 주기에 자동 실행됨을 로그로 확인
- [ ] 기존 `cron hour=18` 설정 유지

---

### [FIX-2] AI 분류 일관성 개선 ⚠ 높음

**문제**: 동일 저장소(`anthropic-sdk-python`) 연속 릴리즈가 `harness`, `orchestration`,
`integration`, `harness` 4개 카테고리로 분산. OpenAI Codex 글이 `claude_code`로 오분류.

**변경 파일**: `backend/app/services/ai_processor.py` — `_SYSTEM_PROMPT`

**개선 방향**:

1. **카테고리별 부정 예시 추가** — 각 카테고리에 "이런 건 제외" 명시:
   ```
   * claude_code: Anthropic의 Claude Code CLI 전용. OpenAI·Google 관련 콘텐츠는
     claude_code로 분류하지 않는다. 단순 anthropic-sdk 업데이트도 claude_code가 아닌
     integration으로 분류한다.
   ```

2. **SDK 릴리즈 분류 규칙 명시화**:
   ```
   * anthropic-sdk-python / anthropic-sdk-js 릴리즈 → integration
   * claude-code CLI 릴리즈 → claude_code
   * MCP 서버 업데이트 → integration (MCP 서버 자체) 또는 claude_code (Claude Code 훅/설정)
   ```

3. **few-shot 예시 2~3개 추가** (프롬프트 끝 부분):
   ```
   예시:
   - "anthropic-sdk-python v0.50" → integration (SDK 업데이트)
   - "Claude Code v2.1.141 released" → claude_code (CLI 릴리즈)
   - "LangChain v0.3 agents" → agents (서드파티 에이전트 프레임워크)
   ```

**완료 조건**:
- [ ] 동일 저장소 연속 릴리즈 3개가 같은 카테고리로 분류됨
- [ ] OpenAI/Google 관련 항목이 `claude_code`로 분류되지 않음

---

### [FIX-3] feedparser 동기 블로킹 해결 ⚠ 중간

**문제**: `feedparser.parse()`가 async 함수 내에서 동기 I/O를 수행하며 이벤트 루프를 블로킹.
RSS 소스 6개 순차 실행 시 최대 수십 초 블로킹 가능.

**변경 파일**: `backend/app/services/crawler.py`

```python
# Before
feed = feedparser.parse(source["url"])

# After
import asyncio
loop = asyncio.get_event_loop()
feed = await loop.run_in_executor(None, feedparser.parse, source["url"])
```

**완료 조건**:
- [ ] `run_in_executor` 래핑 후 동시 RSS 수집 시 이벤트 루프 블로킹 없음

---

### [FIX-4] GitHub API 레이트 리밋 처리 ⚠ 중간

**문제**: 403 응답을 `logger.error`로만 처리. 토큰 없이 9개 레포 호출 시 60 req/h 초과 가능.
실패한 레포 데이터가 수집 없이 누락됨.

**변경 파일**: `backend/app/services/crawler.py`

- `X-RateLimit-Remaining` 헤더 확인 → 0이면 `X-RateLimit-Reset`까지 대기
- 403/429 응답 시 지수 백오프(1초 → 2초 → 4초) 재시도 최대 3회
- `GITHUB_TOKEN` 미설정 경고를 startup 로그에 추가

**완료 조건**:
- [ ] 403 응답 시 재시도 로그 확인
- [ ] 레이트 리밋 소진 시 대기 후 재개

---

### [FIX-5] 크롤러 실행 후 Redis 캐시 무효화 ⚠ 중간

**문제**: 신규 항목 추가·Admin 수정 후 최대 5분간 구버전 데이터 반환.
`categories`, `timeline` 캐시가 크롤 완료 후에도 만료 전까지 유지됨.

**변경 파일**: `backend/app/cache.py`, `backend/app/services/crawler.py`, `backend/app/routers/admin.py`

- `cache.py`에 `cache_delete(key: str)` 함수 추가
- `run_crawl_with_log()` 완료 후 `cache_delete("categories")`, `cache_delete("timeline")` 호출
- Admin 항목 수정/삭제 엔드포인트에서도 캐시 무효화

**완료 조건**:
- [ ] 크롤 직후 `/api/categories` 요청 시 신규 카테고리 즉시 반영

---

### [FIX-6] 홈 화면 중복 노출 제거 ⬇ 낮음

**문제**: 메인 피드의 `LatestTechList`(최근 20개)와 `RecentTimeline`(최근 15개) 모두
`updated_at` 역순 동일 데이터를 두 번 표시.

**변경 파일**: `frontend/src/app/page.tsx`

- `RecentTimeline`을 제거하거나 별도 "이 주의 트렌드" 섹션으로 분리
- 또는 타임라인을 날짜 기준 그룹핑(오늘/어제/이번 주)으로 대체하여 중복 방지

**완료 조건**:
- [ ] 메인 페이지에서 동일 항목이 두 컴포넌트에 동시 노출되지 않음

---

## 이후 백로그 (스프린트 3 이후)

### P1 — 안정성

**[P1-1] Alembic 마이그레이션 도입**
- `alembic init`, `env.py` 설정, 초기 마이그레이션 생성
- `create_tables()` → `alembic upgrade head` 방식으로 교체
- `claude_code` Enum이 이미 수동 적용된 상태이므로 초기 migration은 현재 스키마 기준으로 생성

**[P1-2] Deprecated 추적 강화** ⭐ 핵심 차별화 기능
- 현재 DB에 deprecated 후보가 1건뿐 — 핵심 기능이 사실상 미작동 상태
- AI 분류 개선([FIX-2])과 함께 deprecated 감지 프롬프트 보강
- Admin ReviewQueue 처리 UI 개선 (승인/거부 + 사유 입력)
- deprecated 확정 시 관련 항목 자동 연결 (`replaces_id` 필드 활용)

### P2 — 기능 완성

**[P2-1] 기술 상세 페이지 정보 보강**
- 현재 상세 페이지: 제목·요약·카테고리·날짜만 표시 — 방문 이유가 없음
- `raw_content` 전문 표시 (마크다운 렌더링)
- 관련 항목("같은 카테고리 최근 5개") 섹션 추가
- 소스 링크를 눈에 띄는 CTA 버튼으로 변경

**[P2-2] 검색 관련도 정렬**
- 현재: `ILIKE` 부분일치 + `updated_at` 역순 — 관련도 없음
- PostgreSQL `ts_rank` 또는 제목 일치 가중치 적용
- `raw_content`/`description` 본문까지 검색 범위 확장

**[P2-3] CategoryCount 타입 완성**
- `types.ts`의 `CategoryCount`에 `active_count`, `deprecated_count` 필드 추가
- `CategoryNav.tsx`에서 deprecated 수 배지 표시

### P3 — 고도화

**[P3-1] RSS 피드 제공 (`/feed.xml`)**  
**[P3-2] 자동 Deprecated 확정 (신뢰도 임계값)**  
**[P3-3] 이메일 뉴스레터 (Resend API)**  
**[P3-4] 기술 비교 페이지 (`/compare?a=id1&b=id2`)**

---

## 콘텐츠 분류 체계 (업데이트)

| 카테고리 | 한국어 | 한 줄 설명 | 대표 예시 |
|---------|--------|----------|---------|
| `skills` | 스킬 | AI 능력 단위, 기능 확장 플러그인 | Code Review, PDF, PPTX Skill |
| `harness` | 하네스 | AI 실행환경·프레임워크 | Claude Code Harness, LangChain |
| `agents` | 에이전트 | 자율 다단계 태스크 실행 AI | Claude Agent SDK, AutoGPT, CrewAI |
| `orchestration` | 오케스트레이션 | 다중 에이전트 조율 | Multi-agent, AutoGen, Swarm |
| `integration` | 인테그레이션 | AI-외부 도구 연결 | MCP, Tool Use, RAG |
| `prompting` | 프롬프팅 | 더 나은 AI 응답을 위한 입력 기법 | CoT, ReAct, Prompt Caching |
| `infra` | 인프라/운영 | AI 시스템 배포·비용·관측성 | 토큰 최적화, LLMOps |
| `claude_code` | Claude Code | Claude Code CLI 전용 업데이트 (**신규**) | 스킬 릴리즈, MCP 서버, hooks |

| 상태 | 설명 |
|------|------|
| `active` | 현재 권장 |
| `stable` | 안정적이지만 더 나은 대안 존재 |
| `deprecated` | 상위 호환 기술로 완전 대체됨 |
| `experimental` | 베타·실험 단계 |

---

## 기술스택 (변경 없음)

| 레이어 | 기술 |
|--------|------|
| 백엔드 | FastAPI (Python 3.12+) |
| 크롤러 | feedparser + httpx + APScheduler |
| AI 처리 | claude-haiku-4-5-20251001 (프롬프트 캐싱 적용) |
| DB | PostgreSQL (asyncpg + SQLAlchemy 2.0) |
| 캐시 | Redis |
| 프론트엔드 | Next.js 15 App Router (TypeScript strict) |
| 스타일링 | Tailwind CSS v4 |
| 배포 | Railway (백엔드) + Vercel (프론트엔드) |
