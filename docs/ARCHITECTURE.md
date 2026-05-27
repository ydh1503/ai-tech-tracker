# 아키텍처 문서

---

## 시스템 개요

**크롤러 → AI 처리 → DB → API → 프론트엔드** 순서로 데이터가 흐르는 단방향 파이프라인.
백엔드(FastAPI, Railway)와 프론트엔드(Next.js, Vercel)를 독립 배포한다.

### 핵심 설계 결정

1. **백엔드/프론트엔드 완전 분리**: Railway는 Python 상주 프로세스 지원(APScheduler 크론 가능), Vercel은 Next.js Serverless에 최적화
2. **Deprecated 2단계 승인**: 크롤러 자동 감지 → ReviewQueue 삽입 → 관리자 확인 → 상태 변경 (오판 방지)
3. **기술 항목 보존**: deprecated 상태가 되어도 삭제하지 않음 — 역사적 맥락 유지
4. **서버 컴포넌트 우선**: Next.js에서 클라이언트 번들 최소화, SEO 유리
5. **프롬프트 캐싱**: `ai_processor.py`에서 시스템 프롬프트에 `cache_control: ephemeral` 적용 — 배치 처리 비용 절감

---

## 아키텍처 다이어그램

```
외부 소스
  ├── RSS 피드 (Anthropic, OpenAI, HN, O'Reilly, GitHub Blog)
  ├── GitHub API (릴리즈 이벤트)
  └── 웹 크롤링 (httpx)
         │
         ▼
[백엔드 — Railway]
  APScheduler (매일 18:00 UTC = KST 03:00)
         │
  CrawlerService (feedparser + httpx)
         │
  AI Processor (Claude Haiku, 배치 10개 병렬, 프롬프트 캐싱)
         │ is_relevant=true인 항목만
         ▼
[데이터 계층]
  PostgreSQL: TechItem, CrawlLog, ReviewQueue
  Redis:      categories (TTL 300s), timeline (TTL 300s)
         │
  FastAPI REST API (/api/*)
         │
         ▼
[프론트엔드 — Vercel]
  Next.js 15 App Router
  서버 컴포넌트 → 백엔드 API 직접 호출
  클라이언트 컴포넌트: SearchBar.tsx, admin/page.tsx
```

---

## 계층 구조

### 백엔드 레이어

```
app/
├── config.py          — pydantic-settings 기반 환경변수 (.env → Python 객체)
├── database.py        — 비동기 세션 팩토리 + create_tables() (SQLAlchemy auto create)
├── cache.py           — Redis 헬퍼 (cache_get / cache_set / [미구현] cache_delete)
├── models/tech.py     — TechItem, CrawlLog, ReviewQueue ORM 모델
├── schemas/tech.py    — Pydantic 요청/응답 스키마 (모델과 분리)
├── routers/
│   ├── tech.py        — 공개 API (/api/tech, /api/categories, /api/feed/timeline)
│   └── admin.py       — 관리자 API (/api/admin/*), Bearer 토큰 인증
└── services/
    ├── crawler.py     — RSS + GitHub 수집 파이프라인
    ├── ai_processor.py— Claude API 배치 처리 (BATCH_SIZE=10)
    └── scheduler.py   — APScheduler BackgroundScheduler
```

**의존 방향**: `routers` → `services` → `models/schemas`

### 프론트엔드 레이어

```
src/
├── app/           — Next.js App Router (서버 컴포넌트 기본)
│   ├── layout.tsx         — 공통 헤더/푸터 (ThemeProvider, Atom 피드 링크)
│   ├── page.tsx           — / 메인 피드 (패치 그룹화, FilterBar)
│   ├── category/[slug]/   — /category/:slug (설명 헤더 + FilterBar)
│   ├── tech/[id]/         — /tech/:id 상세 (raw_content 접기, siblings)
│   ├── deprecated/        — /deprecated
│   ├── search/            — /search?q= (FTS 기반)
│   ├── compare/           — /compare?a=ID&b=ID 기술 비교
│   └── admin/             — /admin ("use client")
├── components/
│   ├── TechCard, TechGroupCard, PatchVersionViewer  — 카드 계열
│   ├── StatusBadge, DeprecatedBanner                — 상태 표시
│   ├── SearchBar (자동완성), FilterBar, Pagination   — 탐색 UI
│   ├── CategoryNav (deprecated 배지 포함), Timeline  — 내비게이션
│   └── ThemeToggle, ThemeProviderWrapper            — 테마 토글
└── lib/
    ├── api.ts     — apiFetch 래퍼 (SSR/CSR URL 분기) + 정규화 함수
    └── types.ts   — TechItem, Category, Status, CategoryCount, CATEGORY_META
```

**클라이언트 컴포넌트** (`"use client"` 선언): `SearchBar.tsx`, `FilterBar.tsx`, `ThemeToggle.tsx`, `ThemeProviderWrapper.tsx`, `PatchVersionViewer.tsx`, `admin/page.tsx`.

---

## 데이터 흐름

### 크롤링 파이프라인 (매일 18:00 UTC)

```
1. AsyncIOScheduler → run_crawl_with_log() (직접 코루틴 스케줄링)
2. RSS 수집: feedparser.parse()를 run_in_executor()로 비동기 래핑 (이벤트 루프 블로킹 방지)
   → 6개 소스: Hacker News, O'Reilly Radar, GitHub Blog, Anthropic Blog, OpenAI Blog, Google Developers Blog
   → RSS entry에서 tech_released_at(published_parsed) 추출
3. GitHub 수집: /repos/{owner}/{repo}/releases?per_page=10 (9개 레포)
   → 403/429 시 지수 백오프(1→2→4초) 재시도 최대 3회
   → published_at → tech_released_at 변환
4. source_url UNIQUE 중복 필터링 + 제목 소프트 중복 감지(_is_soft_duplicate)
5. 신규 항목 Claude Haiku API 전송 (BATCH_SIZE=10 병렬, 프롬프트 캐싱 적용)
   → is_relevant=false 항목 버림
   → is_relevant=true 항목: category, summary, description(한국어 500자), is_deprecated_candidate 추출
6. TechItem INSERT
   → status = _infer_status(title, tag): alpha/beta/rc/pre/preview/experimental/-dev/.dev → experimental
   → description = AI 생성 한국어 활용 설명 (영어 원문은 raw_content에 보존)
   → tech_released_at = 기술 자체 출시일
   → is_deprecated_candidate=true이면 ReviewQueue INSERT
7. CrawlLog 기록 (소스별 SourceResult 집계)
8. Redis 캐시 무효화: cache_delete("categories"), cache_delete("timeline")
```

### 사용자 요청 흐름 (기술 상세 페이지)

```
1. 브라우저 → /tech/[id]
2. Vercel Next.js 서버: app/tech/[id]/page.tsx (서버 컴포넌트)
3. fetchTechById(id) → GET /api/tech/{id}
4. FastAPI → PostgreSQL: TechItem + deprecated_by_item (selectin 로드)
5. JSON 응답 → normalizeTechItem() → TechItem 타입으로 정규화
6. HTML 렌더링 (SSR), status==="deprecated"이면 <DeprecatedBanner> 포함
```

### 관리자 Deprecated 승인 흐름

```
1. /admin → 토큰 입력 → fetchAdminQueue(token) → GET /api/admin/queue?reviewed=false
2. 큐 항목 목록 렌더링
3. "확정" 클릭 → POST /api/admin/queue/{id}/approve
   → TechItem.status = "deprecated"
   → TechItem.deprecated_reason, deprecated_at 업데이트
   → ReviewQueue.reviewed = true, approved = true
4. 이후 /tech/{id} 페이지에서 <DeprecatedBanner> 노출
```

---

## API 설계

- **스타일**: REST (JSON)
- **경로 prefix**: `/api/` (admin은 `/api/admin/`)
- **인증**: 공개 API 인증 없음 / 관리자 API `Authorization: Bearer {ADMIN_TOKEN}`
- **API 문서**: http://localhost:8000/docs (Swagger UI)

### 엔드포인트 목록

| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| `GET` | `/api/tech` | 목록 (페이지네이션, category/status/created_after 필터) | 없음 |
| `GET` | `/api/tech/deprecated` | deprecated 목록 (대체 기술 포함) | 없음 |
| `GET` | `/api/tech/search` | FTS 검색 (`?q=`, ILIKE 폴백) | 없음 |
| `GET` | `/api/tech/autocomplete` | 제목 prefix 자동완성 (최대 5개) | 없음 |
| `GET` | `/api/tech/grouped` | 패치 버전 그룹화 목록 | 없음 |
| `GET` | `/api/tech/{id}` | 상세 | 없음 |
| `GET` | `/api/tech/{id}/siblings` | 같은 major.minor 패치 버전 목록 | 없음 |
| `GET` | `/api/categories` | 카테고리별 항목 수 (Redis 캐시) | 없음 |
| `GET` | `/api/feed/timeline` | 최근 업데이트 50개 (Redis 캐시) | 없음 |
| `GET` | `/api/feed.xml` | 전체 Atom 1.0 RSS 피드 (최근 20개) | 없음 |
| `GET` | `/api/feed/{category}.xml` | 카테고리별 Atom RSS 피드 | 없음 |
| `GET` | `/api/admin/queue` | deprecated 검토 큐 | Bearer |
| `POST` | `/api/admin/queue/{id}/approve` | deprecated 승인 | Bearer |
| `POST` | `/api/admin/queue/{id}/reject` | deprecated 거부 | Bearer |
| `POST` | `/api/admin/tech` | 수동 추가 | Bearer |
| `PATCH` | `/api/admin/tech/{id}` | 수정 | Bearer |
| `DELETE` | `/api/admin/tech/{id}` | 삭제 | Bearer |
| `GET` | `/api/admin/crawl/logs` | 크롤링 로그 | Bearer |
| `POST` | `/api/admin/crawl/trigger` | 수동 크롤 트리거 (202 Accepted, 비동기) | Bearer |

---

## DB 설계

### ERD

```
TechItem (1) ──── (N) ReviewQueue
    │
    └── self-referencing FK: deprecated_by → TechItem.id (SET NULL on delete)
```

### tech_items 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | UUID PK | |
| `title` | VARCHAR(500) | 기술명, INDEX |
| `description` | TEXT | AI 생성 한국어 활용 설명 (500자 이내, 독자 관점 재해석) |
| `summary` | VARCHAR(500) | AI 생성 한국어 한 줄 요약 |
| `category` | ENUM | skills/harness/agents/orchestration/integration/prompting/infra/claude_code, INDEX |
| `status` | ENUM | active/stable/deprecated/experimental, INDEX |
| `official_url` | VARCHAR(2048) | 공식 문서 링크 |
| `source_url` | VARCHAR(2048) UNIQUE | 원본 출처 (중복 감지 기준), INDEX |
| `raw_content` | TEXT | 원시 수집 내용 (최대 5000자) |
| `deprecated_by` | UUID FK → tech_items.id | 대체 기술 (자기참조, SET NULL) |
| `deprecated_reason` | TEXT | 대체 이유 |
| `deprecated_at` | TIMESTAMPTZ | 지원 종료 일시 |
| `tech_released_at` | TIMESTAMPTZ | 기술 자체 출시일 (RSS/GitHub published_at에서 추출) |
| `search_vector` | TSVECTOR | FTS 인덱스용 (`simple` 사전, GIN 인덱스, 트리거 자동 갱신) |
| `created_at` | TIMESTAMPTZ | DB 등록일 |
| `updated_at` | TIMESTAMPTZ | 마지막 수정일 |

### crawl_logs 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | UUID PK | |
| `crawled_at` | TIMESTAMPTZ | 크롤링 실행 시각 |
| `source` | VARCHAR(2048) | 수집 소스 목록 (쉼표 구분) |
| `items_found` | INTEGER | 발견된 항목 수 |
| `items_added` | INTEGER | 신규 추가된 항목 수 |
| `items_updated` | INTEGER | 업데이트된 항목 수 |
| `error` | TEXT | 오류 메시지 (없으면 null) |

### review_queue 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | UUID PK | |
| `tech_item_id` | UUID FK → tech_items.id (CASCADE) | 검토 대상, INDEX |
| `suggested_deprecated_by` | UUID FK → tech_items.id (SET NULL) | 제안된 대체 기술 |
| `reason` | TEXT | 감지 이유 (키워드 또는 AI 응답) |
| `detected_at` | TIMESTAMPTZ | 감지 시각 |
| `reviewed` | BOOLEAN | 관리자 검토 완료 여부 |
| `reviewed_at` | TIMESTAMPTZ | 검토 시각 |
| `approved` | BOOLEAN\|NULL | 승인(true)/거부(false)/미결(null) |

---

## Deprecated 처리 흐름

```
크롤러 감지 (AI + 휴리스틱 2중 검사)
    │
    ▼
ReviewQueue INSERT (reviewed=false, approved=null)
    │
    ▼
관리자 /admin 페이지 검토
    │
    ├── 승인 → TechItem.status = "deprecated"
    │          TechItem.deprecated_by = 대체 기술 ID (optional)
    │          TechItem.deprecated_reason = 이유
    │          TechItem.deprecated_at = 현재 시각
    │          ReviewQueue.reviewed = true, approved = true
    │
    └── 거부 → ReviewQueue.reviewed = true, approved = false
               TechItem 상태 변경 없음
```

---

## 캐시 전략

| 캐시 키 | TTL | 무효화 시점 |
|---------|-----|-----------|
| `categories` | 300초 | `run_crawl_with_log()` 완료 후 `cache_delete("categories")` 자동 호출 |
| `timeline` | 300초 | `run_crawl_with_log()` 완료 후 `cache_delete("timeline")` 자동 호출 |

Redis 연결 실패 시 캐시를 우회하고 DB에서 직접 조회한다 (graceful degradation).

---

## 보안 고려사항

- **관리자 인증**: `Authorization: Bearer` 헤더 + 환경변수 토큰 단순 비교 (단일 관리자 운영 전제)
- **CORS**: `CORS_ORIGINS` 환경변수로 허용 오리진 명시적 제한
- **환경변수**: `ANTHROPIC_API_KEY`, `ADMIN_TOKEN` 등 민감 정보는 `.env`에만 보관
- **SQL Injection**: SQLAlchemy ORM 파라미터 바인딩으로 자동 방어
- **외부 링크**: `rel="noopener noreferrer"` 적용

---

## 현재 설계의 한계 및 확장 방향

| 한계 | 현재 방식 | 확장 방향 |
|------|---------|---------|
| 검색 성능 | FTS(`simple` 사전) — 한국어 형태소 분리 없음 | `pg_trgm` 또는 별도 한국어 검색엔진 (Elasticsearch 등) |
| DB 마이그레이션 | SQLAlchemy auto create | Alembic 마이그레이션 도입 |
| 크롤러 확장성 | 단일 프로세스 순차 실행 | Celery + Redis Queue 병렬화 |
| 관리자 인증 | 단순 토큰 비교 | JWT + 만료 시간 |
| grouped 쿼리 | 전체 데이터 메모리 로드 후 Python 그룹화 (상한 500건) | SQL REGEXP_REPLACE로 DB 레벨 집계 |
