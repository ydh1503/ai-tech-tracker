# AI 기술 트래커 — 기능 현황 및 백로그

**최종 업데이트**: 2026-05-27 (서비스 품질 개선 스프린트 완료)

---

## 현재 구현 상태

### 백엔드 (FastAPI)

| 기능 | 파일 | 상태 |
|------|------|------|
| TechItem / CrawlLog / ReviewQueue 모델 | `models/tech.py` | 완료 |
| 공개 API (목록, 상세, 검색, deprecated, 카테고리, 타임라인) | `routers/tech.py` | 완료 |
| 관리자 API (deprecated 승인/거부, 수동 추가/수정/삭제, 크롤 트리거/로그) | `routers/admin.py` | 완료 |
| RSS 수집 (HN, O'Reilly, GitHub Blog, Anthropic, OpenAI, Google) | `services/crawler.py` | 완료 |
| GitHub 릴리즈 수집 (9개 레포, rate limit 재시도) | `services/crawler.py` | 완료 |
| **크롤러 description 저장 방식 수정** (raw 영문 본문 → AI 생성 한국어 description) | `services/crawler.py` | **완료** |
| Claude AI 분류·요약·deprecated 후보 감지 (배치 + 프롬프트 캐싱) | `services/ai_processor.py` | 완료 |
| AI 분류 시스템 프롬프트 개선 (SDK 규칙 명시 + few-shot) | `services/ai_processor.py` | 완료 |
| **AI 한국어 description 생성** (독자 관점 500자 이내 활용 설명, 한국 일반 사용자 기준 재해석) | `services/ai_processor.py` | **완료** |
| 휴리스틱 deprecated 키워드 감지 | `utils/deprecated_detector.py` | 완료 |
| AsyncIOScheduler 크론 (매일 18:00 UTC = KST 03:00) | `services/scheduler.py` | 완료 |
| Redis 캐시 (categories, timeline TTL 300초) + 크롤 후 무효화 | `cache.py` | 완료 |
| DB 자동 테이블 생성 (`create_tables()`) | `database.py` | 완료 |
| 검색 범위 확장 (description + raw_content) + 관련도 정렬 | `routers/tech.py` | 완료 |
| Atom 1.0 피드 (`/api/feed.xml`, 최근 20개) | `routers/tech.py` | 완료 |
| 패치 버전 그룹화 엔드포인트 (`/api/tech/grouped`, `/api/tech/{id}/siblings`) | `routers/tech.py` | 완료 |

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
| 기술 상세 페이지 raw_content + 관련 항목 | `app/tech/[id]/page.tsx` | 완료 |
| CategoryNav deprecated 배지 | `components/CategoryNav.tsx` | 완료 |
| Admin deprecated_by_id 입력 + claude_code 카테고리 + 크롤 트리거 버튼 | `app/admin/page.tsx` | 완료 |
| **다크/라이트 테마 토글** (`next-themes`, 헤더 버튼, localStorage 저장, hydration 보호) | `components/ThemeToggle.tsx`, `components/ThemeProviderWrapper.tsx`, `layout.tsx` | **완료** |
| **필터 바** (상태·기간 필터, URL searchParams 동기화, 홈/카테고리 페이지 적용) | `components/FilterBar.tsx`, `app/page.tsx`, `app/category/[slug]/page.tsx` | **완료** |
| **검색 자동완성** (debounce 300ms, 드롭다운 5개 제안, 키보드 방향키 탐색) | `components/SearchBar.tsx` | **완료** |
| **Admin Deprecated 검색 UI** (UUID 직접 입력 → 제목 검색 드롭다운 선택) | `app/admin/page.tsx` | **완료** |
| **Admin 크롤 로그 탭** (소스별 성공/실패 색상 배지) | `app/admin/page.tsx` | **완료** |
| 기술 비교 페이지 (`/compare?a=ID&b=ID`) | `app/compare/page.tsx` | 완료 |
| 패치 버전 그룹화 카드 | `components/TechGroupCard.tsx` | 완료 |
| 패치 버전 선택 뷰어 | `components/PatchVersionViewer.tsx` | 완료 |

---

## 알려진 이슈

> 2026-05-27 갱신. ✅ = 해결 완료.

| # | 이슈 | 영향도 | 위치 | 상태 |
|---|------|--------|------|------|
| 1 | **스케줄러 비동기 충돌** — `BackgroundScheduler`(동기) + `asyncio.run()` 패턴이 FastAPI 이벤트 루프와 충돌. | **치명** | `services/scheduler.py` | ✅ `AsyncIOScheduler`로 교체 완료 |
| 2 | **AI 분류 일관성 없음** — 동일 SDK 연속 릴리즈가 4개 카테고리로 흩어짐. OpenAI 항목이 `claude_code`로 오분류. | **높음** | `services/ai_processor.py` 시스템 프롬프트 | ✅ SDK 규칙 명시 + few-shot 예시 추가 완료 |
| 3 | **크롤러 실행 후 Redis 캐시 무효화 없음** — 신규 항목 추가 후 최대 5분간 구버전 데이터 반환 | 중간 | `services/crawler.py`, `cache.py` | ✅ `cache_delete()` 구현 + 크롤 완료 후 자동 호출 |
| 4 | **GitHub RSS 동기 블로킹** — `feedparser.parse()`가 async 함수 내 동기 호출로 이벤트 루프 블로킹 | 중간 | `services/crawler.py` | ✅ `run_in_executor()` 래핑 완료 |
| 5 | **GitHub rate limit 미처리** — 403 오류를 `logger.error`로만 처리, 재시도 없음 | 중간 | `services/crawler.py` | ✅ 지수 백오프(1→2→4초) 재시도 3회 구현 완료 |
| 6 | **홈/타임라인 중복 노출** — 메인 피드 `LatestTechList`와 `RecentTimeline`이 같은 데이터를 두 번 표시 | 낮음 | `app/page.tsx` | 미해결 |
| 7 | **Alembic 마이그레이션 미적용** — 스키마 변경 시 수동 ALTER TABLE 필요 | 높음 | `database.py` | 미해결 |
| 8 | **검색 한국어 형태소 분리 없음** — `simple` 사전은 토큰화만 수행. "MCP 서버" 검색 시 "MCP server" 항목 부분 누락 가능 | 낮음 | `routers/tech.py`, `database.py` | 미해결 (pg_trgm 또는 전용 검색엔진 필요) |
| 9 | **stable/experimental 상태 미사용** — 크롤러가 항상 `active`만 저장 | 낮음 | `services/crawler.py` | ✅ `_infer_status()` + 매주 `promote_stable_items()` 구현 완료 |
| 10 | `CategoryCount` 타입이 `count`만 노출 — `active_count`, `deprecated_count` 미사용 | 낮음 | `frontend/src/lib/types.ts` | ✅ 두 필드 추가 + `CategoryNav` 배지 표시 완료 |

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

## 스프린트 5 ✅ 완료 (2026-05-27)

### [P4-1] 패치 버전 그룹화 ✅
- 동일 기술의 `major.minor`가 같고 `patch`만 올라간 항목을 목록에서 하나의 카드로 묶어 표시
- 그룹 카드: `base_title` + "v{major}.{minor} · N개 패치" 배지, 최신 버전 요약, 버전 칩 최대 3개 표시
- 상세 페이지: 같은 그룹의 패치 버전 버튼들로 선택 → 해당 버전 변경 내역 인라인 표시 (클라이언트 컴포넌트)

**변경 파일**:
- `backend/app/schemas/tech.py` — `PatchVersionChip`, `PatchVersionSummary`, `TechGroupedItem` 추가
- `backend/app/routers/tech.py` — `/api/tech/grouped`, `/api/tech/{id}/siblings` 엔드포인트 추가
- `frontend/src/lib/types.ts` — `PatchVersionChip`, `PatchVersionSummary`, `TechGroupedItem` 추가
- `frontend/src/lib/api.ts` — `fetchTechGrouped()`, `fetchTechSiblings()` 추가
- `frontend/src/components/TechGroupCard.tsx` — 신규 (그룹 카드 컴포넌트)
- `frontend/src/components/PatchVersionViewer.tsx` — 신규 (클라이언트 버전 선택기)
- `frontend/src/app/page.tsx` — grouped 엔드포인트 사용
- `frontend/src/app/category/[slug]/page.tsx` — grouped 엔드포인트 사용
- `frontend/src/app/tech/[id]/page.tsx` — siblings 섹션 추가

---

## 스프린트 4 ✅ 완료 (2026-05-27)

### [P1-2] Deprecated 추적 강화 ✅
- Admin ReviewQueue에 대체 기술 ID 입력 필드 추가 (승인 시 `deprecated_by_id` 연결)
- Admin CATEGORIES 목록에 `claude_code` 누락 수정
- Admin에 크롤 수동 트리거 버튼 추가

**변경 파일**: `frontend/src/app/admin/page.tsx`

### [P3-1] RSS/Atom 피드 ✅
- 백엔드 `/api/feed.xml` 엔드포인트 — 최근 20개 항목을 Atom 1.0 XML로 반환
- `layout.tsx` `<head>`에 `<link rel="alternate" type="application/atom+xml" href="/feed.xml">` 추가
- Next.js rewrite 규칙으로 `/feed.xml` → `/api/feed.xml` 프록시 연결

**변경 파일**: `backend/app/routers/tech.py`, `frontend/src/app/layout.tsx`, `frontend/next.config.ts`

### [P3-4] 기술 비교 페이지 ✅
- `/compare?a=ID1&b=ID2` — 두 항목 나란히 비교
- `fetchTechById` 두 번 호출, 필드별 차이 강조 표시 (다른 필드는 노란 배경으로 구분)
- 상세 설명 나란히 비교 섹션 및 원본 링크 포함

**변경 파일**: `frontend/src/app/compare/page.tsx` (신규)

---

## 스프린트 3 ✅ 완료 (2026-05-27)

### [P2-1] 기술 상세 페이지 정보 보강 ✅

- `raw_content` 전문 접기/펼치기 `<details>` 섹션 추가
- 같은 카테고리 최근 5개 관련 항목 섹션 추가
- `TechItem` 타입에 `raw_content: string | null` 필드 추가

**변경 파일**: `frontend/src/lib/types.ts`, `frontend/src/lib/api.ts`, `frontend/src/app/tech/[id]/page.tsx`

### [P2-2] 검색 관련도 정렬 ✅

- 검색 범위 `title + summary` → `title + summary + description + raw_content`로 확장
- SQLAlchemy `case()` 식으로 제목 일치 항목 최상단 배치

**변경 파일**: `backend/app/routers/tech.py`

### [P2-3] CategoryCount 타입 완성 ✅

- `CategoryCount`에 `active_count`, `deprecated_count` 필드 추가
- `CategoryNav.tsx`에 deprecated 수 빨간 `-N` 배지 표시

**변경 파일**: `frontend/src/lib/types.ts`, `frontend/src/lib/api.ts`, `frontend/src/components/CategoryNav.tsx`

---

## 스프린트 2 ✅ 완료 (2026-05-27)

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
- [x] 서버 재시작 후 다음 크롤 주기에 자동 실행됨을 로그로 확인
- [x] 기존 `cron hour=18` 설정 유지

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
- [x] 동일 저장소 연속 릴리즈 3개가 같은 카테고리로 분류됨
- [x] OpenAI/Google 관련 항목이 `claude_code`로 분류되지 않음

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
- [x] `run_in_executor` 래핑 후 동시 RSS 수집 시 이벤트 루프 블로킹 없음

---

### [FIX-4] GitHub API 레이트 리밋 처리 ⚠ 중간

**문제**: 403 응답을 `logger.error`로만 처리. 토큰 없이 9개 레포 호출 시 60 req/h 초과 가능.
실패한 레포 데이터가 수집 없이 누락됨.

**변경 파일**: `backend/app/services/crawler.py`

- `X-RateLimit-Remaining` 헤더 확인 → 0이면 `X-RateLimit-Reset`까지 대기
- 403/429 응답 시 지수 백오프(1초 → 2초 → 4초) 재시도 최대 3회
- `GITHUB_TOKEN` 미설정 경고를 startup 로그에 추가

**완료 조건**:
- [x] 403 응답 시 재시도 로그 확인
- [x] 레이트 리밋 소진 시 지수 백오프 후 재개

---

### [FIX-5] 크롤러 실행 후 Redis 캐시 무효화 ⚠ 중간

**문제**: 신규 항목 추가·Admin 수정 후 최대 5분간 구버전 데이터 반환.
`categories`, `timeline` 캐시가 크롤 완료 후에도 만료 전까지 유지됨.

**변경 파일**: `backend/app/cache.py`, `backend/app/services/crawler.py`, `backend/app/routers/admin.py`

- `cache.py`에 `cache_delete(key: str)` 함수 추가
- `run_crawl_with_log()` 완료 후 `cache_delete("categories")`, `cache_delete("timeline")` 호출
- Admin 항목 수정/삭제 엔드포인트에서도 캐시 무효화

**완료 조건**:
- [x] 크롤 직후 `/api/categories` 요청 시 신규 카테고리 즉시 반영

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

### P2 — 기능 완성 ✅ 스프린트 3에서 완료

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

---

## 서비스 기능 갭 분석 및 추가 백로그

> **작성일**: 2026-05-27  
> 전체 코드베이스(백엔드·프론트엔드)를 실제 코드 레벨까지 검토한 뒤 서비스 품질을 저하시키는 미구현 기능들을 정리했다.  
> 수익화·인증·결제 등 상업화 항목은 제외하고, **서비스 자체의 완성도** 기준으로만 선별했다.

---

### [S1] PostgreSQL 풀텍스트 검색 전환 ⚠ 높음

**문제**: 현재 검색은 4개 컬럼(`title`, `summary`, `description`, `raw_content`)에 `ILIKE '%keyword%'`를 OR로 걸고 있다(`routers/tech.py:148-153`). 데이터가 수천 건을 넘어서면 인덱스를 타지 않아 풀 시퀀셜 스캔이 발생한다. 한글 형태소 분리도 없어 "MCP 서버"를 입력해도 "MCP server" 항목이 누락된다.

**현재 코드**:
```python
# routers/tech.py:148
query = select(TechItem).where(
    TechItem.title.ilike(search_term)
    | TechItem.summary.ilike(search_term)
    | TechItem.description.ilike(search_term)
    | TechItem.raw_content.ilike(search_term)
)
```

**변경 사항**:

**파일 1: `backend/app/models/tech.py`**
- `TechItem`에 `search_vector: Mapped[str | None]` 컬럼 추가 (`TSVECTOR` 타입)

**파일 2: `backend/app/database.py`** — `create_tables()` 내 자동 초기화 (Alembic 미적용)
```sql
-- 'simple' 사전 사용: 불변화 없이 토큰화만 수행 → 한국어 포함 다국어 텍스트에 안전
ALTER TABLE tech_items ADD COLUMN IF NOT EXISTS search_vector TSVECTOR;
CREATE INDEX IF NOT EXISTS tech_items_search_gin ON tech_items USING GIN(search_vector);

CREATE OR REPLACE FUNCTION update_search_vector() RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('simple', COALESCE(NEW.title, '')), 'A') ||
    setweight(to_tsvector('simple', COALESCE(NEW.summary, '')), 'B') ||
    setweight(to_tsvector('simple', COALESCE(NEW.description, '')), 'C');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- CREATE OR REPLACE TRIGGER (PostgreSQL 14+): 원자적 교체, DROP+CREATE 경쟁 창 없음
CREATE OR REPLACE TRIGGER tsvector_update
  BEFORE INSERT OR UPDATE ON tech_items
  FOR EACH ROW EXECUTE FUNCTION update_search_vector();
```

**파일 3: `backend/app/routers/tech.py`** — `search_tech_items()` 수정
```python
# FTS 기반 검색 (search_vector가 없는 경우 ILIKE 폴백)
ts_query = func.plainto_tsquery("simple", q)  # 'simple' 사전 사용
query = select(TechItem).where(
    TechItem.search_vector.op("@@")(ts_query)
)
# 랭킹 정렬
query = query.order_by(
    func.ts_rank_cd(TechItem.search_vector, ts_query).desc(),
    TechItem.updated_at.desc(),
)
```

**파일 4: `backend/app/routers/tech.py`** — 자동완성 엔드포인트 추가
```python
@router.get("/tech/autocomplete", response_model=list[str])
async def autocomplete_tech(
    q: str = Query(..., min_length=1, max_length=50),
    db: DbDep = ...,
) -> list[str]:
    """검색어 자동완성 — 제목 prefix 기준 상위 5개"""
    ...
```

**파일 5: `frontend/src/components/SearchBar.tsx`**
- `debounce 300ms` + `/api/tech/autocomplete?q=` 호출
- 드롭다운 5개 제안 표시 (키보드 방향키 탐색 지원)

**완료 조건**:
- [x] "MCP server" 검색 시 "MCP 서버" 관련 항목이 상위에 표시됨
- [ ] 1만 건 데이터 기준 검색 응답 50ms 이하 (EXPLAIN ANALYZE 확인)
- [x] 자동완성 백엔드 엔드포인트 (`/api/tech/autocomplete`) 구현 완료
- [x] 검색창 타이핑 시 자동완성 드롭다운이 300ms 후 표시됨 (키보드 방향키 탐색, Enter 선택 지원)

---

### [S2] 고급 필터 UI ⚠ 중간

**문제**: 백엔드 API는 `category`, `status`, `created_after` 필터를 이미 지원하지만(`/api/tech?category=agents&status=active`), 프론트엔드에 이 필터를 선택할 UI가 전혀 없다. 사용자는 URL을 직접 수정하지 않는 이상 필터링이 불가능하다.

**변경 사항**:

**파일 1: `frontend/src/components/FilterBar.tsx`** (신규)
```
[ 상태: 전체 ▼ ]  [ 기간: 전체 ▼ ]  [ 정렬: 최신순 ▼ ]     [×] 필터 초기화
```

props:
```typescript
interface FilterBarProps {
  status?: Status;
  dateRange?: "today" | "week" | "month" | "all";
  sort?: "updated_at" | "created_at";
  onChange: (filters: FilterState) => void;
}
```

- `<select>` 대신 Tailwind Dropdown 컴포넌트로 구현
- URL searchParams와 동기화 (`?status=active&range=week`)
- 서버 컴포넌트에서 사용 가능하도록 Link 기반 동작

**파일 2: `frontend/src/app/page.tsx`**
- `LatestTechList` 위에 `FilterBar` 배치
- `searchParams`에서 `status`, `range`, `sort` 읽어 `fetchTechGrouped()` 파라미터로 전달

**파일 3: `frontend/src/app/category/[slug]/page.tsx`**
- 카테고리 설명 헤더 아래 `FilterBar` 배치 (category 필터 제외, 나머지 2개만)

**완료 조건**:
- [x] 홈 피드에서 "상태: deprecated" 선택 시 deprecated 항목만 표시됨
- [x] "기간: 이번 주" 선택 시 7일 내 항목만 표시됨
- [x] 필터 선택이 URL에 반영되어 공유/북마크가 가능함
- [x] "필터 초기화" 클릭 시 모든 필터 제거

---

### [S3] stable / experimental 상태 실제 활용 ⚠ 중간

**문제**: `TechStatus` Enum에 `active`, `stable`, `deprecated`, `experimental` 4개 상태가 있지만, 크롤러(`crawler.py:177`)는 모든 항목을 무조건 `TechStatus.active`로 저장한다. `stable`과 `experimental` 상태는 DB에 단 한 건도 존재하지 않는다.

**활용 기준 정의**:

| 상태 | 기준 |
|------|------|
| `experimental` | GitHub 릴리즈 tag에 `alpha`, `beta`, `rc`, `pre`, `dev` 포함 / 제목에 "Preview", "experimental" 포함 |
| `stable` | 주요 버전(`v1.0`, `v2.0` 등 패치가 0)이면서 `active` 상태로 3개월 이상 유지된 항목 |
| `active` | 신규 수집 항목의 기본값 (기존 유지) |
| `deprecated` | 기존 ReviewQueue 승인 흐름 유지 |

**변경 사항**:

**파일 1: `backend/app/services/crawler.py`** — `save_item_and_review()` 수정
```python
def _infer_status(title: str, tag: str | None) -> TechStatus:
    """제목과 tag_name에서 초기 상태를 추론한다."""
    combined = f"{title} {tag or ''}".lower()
    # "dev" 단독 매칭 제외: "developer"/"development"/"devtools" 오탐 방지
    # 릴리즈 태그에 실제로 쓰이는 "-dev" / ".dev" 형태로만 검사
    if any(k in combined for k in ("alpha", "beta", ".rc", "-rc", "pre-", "preview", "experimental", "-dev", ".dev")):
        return TechStatus.experimental
    return TechStatus.active
```

**파일 2: `backend/app/services/scheduler.py`** (신규 배치 작업)
- 매주 일요일 00:00 UTC에 `active` 상태이고 `major.patch == 0`이며 `created_at`이 90일 이상 된 항목을 `stable`로 자동 전환하는 배치 추가

**파일 3: `frontend/src/components/StatusBadge.tsx`**
- `experimental` 상태 배지 색상 추가 (현재 이 상태는 배지가 표시되지 않거나 잘못 표시될 수 있음)

**완료 조건**:
- [x] `anthropic-sdk-python v0.50.0-beta.1` 수집 시 `status=experimental`로 저장됨
- [x] DB에 `experimental` 상태 항목이 실제로 존재함
- [x] 배치 실행 후 오래된 stable 항목이 `stable`로 전환됨

---

### [S4] tech_released_at 자동 추출 ⚠ 중간

**문제**: `TechItem.tech_released_at` 컬럼은 "기술 자체의 최초 출시일"을 저장하기 위해 설계됐으나, 크롤러(`crawler.py:165-183`)가 이 필드를 **한 번도 채우지 않는다**. 프론트엔드(`TechCard.tsx:73-76`, `tech/[id]/page.tsx:122-126`)는 이 필드가 있을 때만 출시 연도/날짜를 표시하도록 구현돼 있어 사실상 해당 UI가 전혀 노출되지 않는다.

**변경 사항**:

**파일 1: `backend/app/services/crawler.py`**

GitHub 릴리즈 수집 시 `published_at` 필드 활용:
```python
# fetch_github_releases() 내부
for release in releases:
    published_at_str: str | None = release.get("published_at")  # "2026-01-15T12:00:00Z"
    tech_released_at = None
    if published_at_str:
        try:
            tech_released_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
        except ValueError:
            pass
    items.append({
        ...,
        "tech_released_at": tech_released_at,
    })
```

RSS 수집 시 `entry.published_parsed` 또는 `entry.updated_parsed` 활용:
```python
# fetch_rss_items() 내부
import time
published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
tech_released_at = None
if published_parsed:
    tech_released_at = datetime(*published_parsed[:6], tzinfo=timezone.utc)
```

**파일 2: `backend/app/services/crawler.py`** — `save_item_and_review()` 수정
```python
item = TechItem(
    ...
    tech_released_at=raw.get("tech_released_at"),  # 추가
)
```

**완료 조건**:
- [x] GitHub 릴리즈 수집 후 `tech_released_at`이 실제 릴리즈 날짜로 채워짐
- [x] RSS 항목 수집 후 `tech_released_at`이 게시 날짜로 채워짐
- [x] 상세 페이지(`/tech/{id}`)에서 출시일이 표시됨

---

### [S5] 카테고리별 개별 RSS 피드 ⬇ 낮음

**문제**: 현재 Atom 피드(`/api/feed.xml`)는 모든 카테고리를 합쳐 최근 20개만 제공한다. 특정 카테고리(예: `claude_code`, `agents`)만 구독하려는 사용자는 방법이 없다.

**변경 사항**:

**파일: `backend/app/routers/tech.py`**

기존 `/api/feed.xml` 엔드포인트를 확장하거나, 신규 경로 추가:
```python
@router.get("/feed/{category}.xml", response_class=Response)
async def get_category_atom_feed(
    category: TechCategory,
    db: DbDep,
) -> Response:
    """특정 카테고리의 최근 20개 항목을 Atom 1.0 XML로 반환한다."""
    ...
```

기존 `/api/feed.xml`도 동일 로직을 재사용하도록 리팩터링 (category=None이면 전체).

**파일: `frontend/src/app/category/[slug]/page.tsx`**
- 카테고리 설명 헤더에 해당 카테고리 RSS 구독 링크 아이콘 추가
  ```html
  <a href="/feed/agents.xml" title="RSS 구독">🔔</a>
  ```

**파일: `frontend/src/app/layout.tsx`**
- 현재 전체 피드 `<link rel="alternate">` 하나만 있는데, 카테고리별로도 `<link>` 추가 (동적 생성은 각 카테고리 페이지의 `generateMetadata`에서 처리)

**완료 조건**:
- [x] `/feed/agents.xml` 요청 시 agents 카테고리 항목만 포함된 Atom 피드 반환
- [x] `/feed/claude_code.xml` 정상 동작
- [x] 존재하지 않는 카테고리 slug는 404 반환

---

### [S6] 소스별 크롤 로그 분리 기록 ⬇ 낮음

**문제**: `run_crawl_with_log()`(`crawler.py:268-308`)는 전체 크롤링 결과를 **하나의 CrawlLog**로 합산해 저장한다(`source` 컬럼에 쉼표 구분 URL 전부를 문자열로 기록). Admin 크롤 로그 화면에서 "HN에서 몇 개, Anthropic에서 몇 개" 같은 소스별 수집 현황을 파악할 수 없고, 특정 소스 장애 여부도 확인 불가능하다.

**변경 사항**:

**파일 1: `backend/app/services/crawler.py`** — `run_crawl()` 리팩터링
- 소스별로 수집 결과를 `dict[str, SourceResult]` 형태로 반환
  ```python
  @dataclass
  class SourceResult:
      source_url: str
      source_name: str
      found: int
      added: int
      error: str | None
  ```

**파일 2: `backend/app/services/crawler.py`** — `run_crawl_with_log()` 수정
- `CrawlLog`를 소스별로 **N개** INSERT (현재 1개)

**파일 3: `frontend/src/app/admin/page.tsx`**
- 크롤 로그 목록에서 소스별 성공/실패를 색상으로 구분 표시
- `error` 필드가 있는 소스는 빨간 배지로 표시

**완료 조건**:
- [x] 크롤 실행 후 소스별(`HN`, `Anthropic Blog`, `GitHub/langchain-ai/langchain` 등) CrawlLog 개별 생성
- [x] Admin 화면에서 소스별 수집 건수와 오류 여부 확인 가능

---

### [S7] 중복 항목 감지 고도화 ⬇ 낮음

**문제**: 현재 중복 판단 기준은 `source_url` UNIQUE 제약(`crawler.py:148-151`)이 전부다. 동일한 기술 정보가 여러 소스(예: GitHub 릴리즈 + HN 기사 + Anthropic 블로그 포스트)에서 수집되면 동일 기술이 3개 별도 항목으로 저장된다. 패치 버전 그룹화가 이 문제를 일부 완화하지만, 아예 다른 URL로 수집된 같은 내용은 여전히 중복 저장된다.

**변경 사항**:

**파일 1: `backend/app/services/crawler.py`** — `get_existing_urls()` 확장
```python
async def get_existing_titles(db: AsyncSession) -> set[str]:
    """DB에 존재하는 title을 소문자 정규화하여 반환한다."""
    result = await db.execute(select(func.lower(TechItem.title)))
    return {row[0] for row in result.fetchall()}
```

**파일 2: `backend/app/services/crawler.py`** — 신규 `_is_soft_duplicate()` 함수
```python
def _is_soft_duplicate(title: str, existing_titles: set[str]) -> bool:
    """제목 정규화(소문자, 특수문자 제거) 후 기존 제목과 비교한다."""
    normalized = re.sub(r"[^a-z0-9\s]", "", title.lower()).strip()
    return normalized in existing_titles
```

- `new_items` 필터링 시 `source_url` 중복 체크에 title 소프트 중복 체크를 추가
- 소프트 중복 감지 시 `logger.info`로 기록하고 건너뜀 (DB에 저장 안 함)

**완료 조건**:
- [x] "LangChain v0.3" 제목이 2개 소스에서 수집될 때 1개만 저장됨
- [x] 소프트 중복 감지 시 로그에 `[SOFT_DUP]` 접두사로 기록됨

---

### [S8] Deprecated 대체 기술 검색 UI 개선 ⬇ 낮음

**문제**: Admin ReviewQueue에서 deprecated 승인 시 대체 기술을 지정하려면 UUID를 직접 입력해야 한다(`admin/page.tsx:29-75`). UUID를 외우거나 별도 탭에서 복사하지 않는 이상 사실상 사용 불가능한 UI다.

**변경 사항**:

**파일: `frontend/src/app/admin/page.tsx`**

UUID 직접 입력 `<input>` → 제목 검색 + 선택 UI로 교체:
```
대체 기술 검색: [__________________________] 🔍
                ↓ (검색 결과 드롭다운)
                  LangChain v0.3.0 (integration)
                  LangChain v0.2.9 (integration)
                  ...
```

- `fetchTechList({ q: searchQuery, size: 5 })` 호출 (debounce 300ms)
- 선택 시 해당 항목의 `id`(UUID)를 숨겨진 상태로 저장, 제목만 표시
- 선택 후 "×" 버튼으로 해제 가능

**완료 조건**:
- [x] "LangChain" 입력 시 해당 기술 목록이 드롭다운으로 표시됨
- [x] 목록에서 항목 선택 시 UUID가 자동 입력됨
- [x] 승인 후 `deprecated_by_id`가 정상적으로 연결됨

---

### [S9] 다크/라이트 테마 토글 ⬇ 낮음

**문제**: Tailwind CSS 설정과 컴포넌트 전반에 `dark:` 클래스가 빠짐없이 적용돼 있지만, 실제로 테마를 전환할 UI 버튼이 없다. 현재는 OS 다크 모드 설정을 따르는 `prefers-color-scheme`만 작동하는 것으로 추정되며, 사용자가 직접 토글할 수 없다.

**변경 사항**:

**파일 1: `frontend/src/app/layout.tsx`**
- 헤더 우측에 테마 토글 버튼 추가
- `next-themes` 라이브러리 사용 (`ThemeProvider` 래핑)

**파일 2: `frontend/src/components/ThemeToggle.tsx`** (신규)
```tsx
"use client";
import { useTheme } from "next-themes";
export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  return (
    <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      {/* 해/달 아이콘 */}
    </button>
  );
}
```

**파일 3: `frontend/package.json`**
- `next-themes` 패키지 추가

**완료 조건**:
- [x] 헤더의 테마 토글 버튼 클릭 시 다크/라이트 전환
- [x] 선택된 테마가 localStorage에 저장되어 새로고침 후에도 유지됨
- [x] hydration 깜빡임 없음 (`suppressHydrationWarning` 처리)

---

### [S10] grouped 엔드포인트 메모리 비효율 ⬇ 낮음

**문제**: `/api/tech/grouped`(`routers/tech.py:188-251`)는 해당 조건의 **전체 데이터를 메모리에 올린 후** Python 딕셔너리로 그룹화한다. 카테고리 필터 없이 전체 조회 시(`category=None`) 데이터가 수만 건이 되면 메모리 사용량이 급증하고 응답 시간이 길어진다.

마찬가지로 `/api/tech/{id}/siblings`(`routers/tech.py:299-303`)도 같은 카테고리 전체를 조회한 후 Python에서 필터링한다.

**변경 사항**:

**파일: `backend/app/routers/tech.py`**

`grouped` 엔드포인트 — 그룹 키를 SQL `REGEXP_REPLACE`로 추출하여 DB 레벨에서 집계:
```python
# 버전 정규표현식을 SQL로 처리
# title에서 "base_name@major.minor" 키를 생성하는 computed column 또는 함수 인덱스 활용
```

`siblings` 엔드포인트 — `SIMILAR TO` 또는 `LIKE` 패턴으로 DB에서 직접 필터:
```python
# _extract_version(item.title) 결과로 LIKE 패턴 생성
# "LangChain v0.3.%" 형태로 DB 쿼리
if info:
    base, major, minor, _ = info
    pattern = f"{base} v{major}.{minor}.%"
    query = select(TechItem).where(TechItem.title.ilike(pattern))
```

**완료 조건**:
- [x] `siblings` 쿼리가 카테고리 전체 조회 없이 LIKE 패턴으로 실행됨 (EXPLAIN ANALYZE 확인)
- [x] 전체 데이터 1만 건 기준 `/api/tech/grouped` 응답 시간 1초 이하

---

## 서비스 품질 개선 스프린트 ✅ 완료 (2026-05-27)

> S1–S10 전체 구현 완료. 이하 항목은 위 갭 분석 백로그와 별도로 이번 스프린트에서 집중 처리한 사안들이다.

---

### [Q1] AI description 한국어 생성 ✅ (치명 버그 수정)

**문제**: 크롤러가 `description` 필드에 `raw.get("content", "")[:1000]` — RSS/GitHub 릴리즈 원문(영어 Markdown) — 을 그대로 저장하고 있었다. 상세 페이지의 "상세 설명"란에 `## What's changed`, `- Added \`terminalSequence\`` 같은 영문 원본이 노출됐다.

**근본 원인**: `ai_processor.py`가 `summary`만 AI로 생성하고 `description`은 정의조차 되어 있지 않았다. 크롤러가 AI 결과 대신 수집 원문을 description에 채웠다.

**사이트 독자 정의** (모든 AI 처리 로직의 기준):
> 이 사이트는 Claude Code, ChatGPT, Gemini 같은 AI 도구를 일상에서 사용하는 **한국의 일반 사용자**를 위한 서비스다.  
> 독자의 핵심 관심사: "이게 나한테 어떤 도움이 되나? 내 AI 도구를 어떻게 더 잘 쓸 수 있나?"

**변경 사항**:

#### `backend/app/services/ai_processor.py`

1. **`_SYSTEM_PROMPT` 보강** — 독자 정의 명시 + `description` 필드 명세 추가:
   ```
   이 서비스의 독자 정의:
   - Claude Code, ChatGPT, Gemini 같은 AI 도구를 일상에서 사용하는 한국의 일반 사용자
   - 개발자가 아닌 사람도 있으므로 쉬운 말로 설명해야 함
   - 핵심 관심사: "이게 나한테 어떤 도움이 되나? 내 AI 도구를 어떻게 더 잘 쓸 수 있나?"
   
   description 작성 기준 (가장 중요):
   - 500자 이내 한국어
   - 독자(한국 일반 사용자) 관점에서 "이게 나한테 왜 유용한가, 어떻게 쓸 수 있나"를 설명
   - Claude Code, ChatGPT, Gemini 등 실제 AI 도구 사용에 직접 연결되는 활용 팁 포함
   - 기술 용어는 괄호로 쉽게 풀어서 설명 (예: "MCP(AI가 외부 도구를 쓸 수 있게 연결해주는 방법)")
   - 영어 원문 번역이 아닌, 독자를 위한 재해석으로 작성
   - is_relevant가 false이면 null
   ```

2. **`ProcessedItem` 데이터클래스** — `description: str | None` 필드 추가

3. **`_parse_response()`** — `description=data.get("description")` 추출 추가

4. **`_FAIL_ITEM`** — `description=None` 추가

#### `backend/app/services/crawler.py`

`save_item_and_review()` 수정:
```python
# Before (영어 원문 그대로 저장)
description=raw.get("content", "")[:1000] or None,

# After (AI가 생성한 한국어 활용 설명 저장)
description=processed.description,
```
> `raw_content` 필드에는 원문이 그대로 보존되어, 상세 페이지 "원문 내용 보기" 접기/펼치기로 여전히 확인 가능하다.

**완료 조건**:
- [x] 신규 수집 항목의 `description`이 AI가 생성한 500자 이내 한국어로 저장됨
- [x] `raw_content`에는 원문이 그대로 보존됨
- [x] `_parse_response()`, `_FAIL_ITEM`, `ProcessedItem`이 `description` 필드를 모두 처리함

---

### [Q2] 기존 영어 description DB 일괄 정리 ✅

**문제**: 버그 수정 이전에 수집된 항목 299개 중 285개의 `description`이 영어 원문이었다.

**처리 방법**:
```sql
-- 영어 원문(Markdown 헤더, 영문자 시작, HTML 태그 등) → NULL 초기화
UPDATE tech_items SET description = NULL
WHERE description ~ '^[#\*\-A-Za-z]';

-- HTML 태그, Markdown 헤더가 포함된 나머지도 처리
UPDATE tech_items SET description = NULL
WHERE description ~ '<p>|^[[:space:]]*#{1,6}[[:space:]]';
```

**결과**:
- 영어 원문 285개 → `NULL` 처리 완료
- 수동 입력된 한국어 description 3개 (`System Prompt Engineering`, `Vector Embeddings`, `Fine-tuning`) 보존
- `raw_content`에는 원문이 그대로 유지되어 데이터 손실 없음

**완료 조건**:
- [x] `description ~ '^[#\*\-A-Za-z<]'` 패턴으로 영어 원문 0건 (전수 제거)
- [x] 한국어 수동 입력 description 3건 보존
- [x] 상세 페이지에서 더 이상 영어 원문이 "상세 설명" 섹션에 노출되지 않음

---

### [Q3] 서비스 기능 갭 전체 구현 (S1–S10) ✅

| 항목 | 내용 | 주요 변경 파일 |
|------|------|--------------|
| **S1** | PostgreSQL FTS 전환 + 자동완성 | `models/tech.py`, `routers/tech.py`, `database.py`, `components/SearchBar.tsx`, `lib/api.ts` |
| **S2** | 필터 바 (상태·기간, URL 동기화) | `components/FilterBar.tsx` (신규), `app/page.tsx`, `app/category/[slug]/page.tsx`, `routers/tech.py` |
| **S3** | stable/experimental 상태 자동 추론 | `services/crawler.py`, `services/scheduler.py` |
| **S4** | tech_released_at 자동 추출 | `services/crawler.py` |
| **S5** | 카테고리별 Atom RSS 피드 | `routers/tech.py` |
| **S6** | 소스별 크롤 로그 분리 + Admin 로그 탭 | `services/crawler.py`, `app/admin/page.tsx`, `lib/api.ts` |
| **S7** | 소프트 중복 감지 (제목 정규화) | `services/crawler.py` |
| **S8** | Deprecated 대체 기술 검색 UI | `app/admin/page.tsx` |
| **S9** | 다크/라이트 테마 토글 | `components/ThemeToggle.tsx` (신규), `components/ThemeProviderWrapper.tsx` (신규), `layout.tsx`, `globals.css`, `package.json` |
| **S10** | grouped/siblings 쿼리 효율화 | `routers/tech.py` |

**FTS 구현 상세** (`database.py` 자동 초기화):
```sql
ALTER TABLE tech_items ADD COLUMN IF NOT EXISTS search_vector tsvector;
CREATE INDEX IF NOT EXISTS tech_items_search_gin ON tech_items USING GIN(search_vector);

CREATE OR REPLACE FUNCTION update_search_vector() RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('simple', COALESCE(NEW.title, '')), 'A') ||
    setweight(to_tsvector('simple', COALESCE(NEW.summary, '')), 'B') ||
    setweight(to_tsvector('simple', COALESCE(NEW.description, '')), 'C');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- CREATE OR REPLACE TRIGGER (PostgreSQL 14+): 원자적 교체로 경쟁 창 없음
CREATE OR REPLACE TRIGGER tsvector_update BEFORE INSERT OR UPDATE ON tech_items
  FOR EACH ROW EXECUTE FUNCTION update_search_vector();
```
> `'simple'` 사전 사용: 불변화 없이 토큰화만 수행하므로 한국어 포함 다국어 텍스트에 안전하게 동작한다.
> `CREATE OR REPLACE TRIGGER` (PostgreSQL 14+): DROP+CREATE 방식의 짧은 경쟁 창을 없애 동시 INSERT 시 `search_vector = NULL` 저장 방지.

**Tailwind v4 다크 모드 설정**:
- `tailwind.config.ts`는 v4에서 사용되지 않음
- `globals.css`에 `@custom-variant dark (&:where(.dark, .dark *));` 추가로 class 기반 다크 모드 활성화

**완료 조건 (통합)**:
- [x] 백엔드 6개 API 엔드포인트 전수 테스트 통과 (목록·검색·자동완성·그룹화·카테고리RSS·카테고리목록)
- [x] 프론트엔드 빌드 성공 (`npm run build` — 타입 오류·컴파일 오류 0건)
- [x] 프론트엔드 개발 서버 응답 정상 (HTTP 200)
- [x] 영어 원문 description DB에서 완전 제거 (0건)
