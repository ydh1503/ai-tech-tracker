# AI 기술 트래커

> AI를 어떻게 더 잘 쓰는가 — 매일 자동으로 수집·분류·업데이트

FastAPI + Next.js 15로 구성된 AI 활용 기술 정보 허브.
RSS, GitHub API로 수집한 원시 정보를 Claude API가 분류·요약하고, Deprecated 기술을 명시적으로 표시한다.

---

## 구현 현황

| 기능 | 상태 |
|------|------|
| RSS / GitHub 수집 + APScheduler AsyncIO (매일 18:00 UTC) | 완료 |
| Claude Haiku AI 분류·요약·한국어 description 생성·deprecated 후보 감지 | 완료 |
| 프롬프트 캐싱 적용 (Anthropic ephemeral cache) | 완료 |
| PostgreSQL CRUD (TechItem, CrawlLog, ReviewQueue) | 완료 |
| Redis 캐시 (categories, timeline, TTL 300초) + **크롤 후 자동 무효화** | 완료 |
| REST API 전체 엔드포인트 (목록·상세·검색·자동완성·그룹화·RSS) | 완료 |
| 관리자 API (Deprecated 승인/거부, 수동 추가/수정, 크롤 트리거/로그) | 완료 |
| Next.js 15 프론트엔드 (메인 피드, 카테고리, 상세, 검색, 비교, admin) | 완료 |
| Deprecated 배너 + 대체 기술 링크 | 완료 |
| Anthropic Blog / MCP 수집 소스 + `claude_code` 카테고리 | 완료 |
| 카테고리 설명 헤더 (카테고리 진입 시 설명 + 예시 표시) | 완료 |
| 페이지네이션 UI (URL 쿼리 파라미터 방식, 홈·카테고리·검색) | 완료 |
| 고급 필터 UI (상태·기간 필터, URL 동기화) | 완료 |
| 다크/라이트 테마 토글 (`next-themes`, localStorage 저장) | 완료 |
| 패치 버전 그룹화 + 버전 선택 뷰어 | 완료 |
| PostgreSQL Full-text Search (tsvector/GIN + `plainto_tsquery('simple')`) | 완료 |
| 검색 자동완성 (debounce 300ms, 드롭다운 5개, 키보드 탐색) | 완료 |
| Atom RSS 피드 (`/feed.xml`, `/feed/{category}.xml`) | 완료 |
| stable/experimental 상태 자동 추론 + 매주 stable 전환 배치 | 완료 |
| tech_released_at 자동 추출 (GitHub published_at / RSS published_parsed) | 완료 |
| 기술 비교 페이지 (`/compare?a=ID&b=ID`) | 완료 |
| Docker Compose 전체 스택 빌드 | 완료 |
| Alembic DB 마이그레이션 | **미적용** (현재 auto create) |

---

## 기술스택

| 분류 | 기술 |
|------|------|
| 백엔드 | Python 3.12+ / FastAPI |
| 크롤링 | feedparser, httpx, APScheduler (AsyncIOScheduler) |
| AI 처리 | claude-haiku-4-5-20251001 (프롬프트 캐싱, 한국어 description 생성) |
| DB | PostgreSQL 17 (asyncpg + SQLAlchemy 2.0, FTS: tsvector/GIN/plainto_tsquery) |
| 캐시 | Redis 7 |
| 프론트엔드 | Next.js 15 (App Router, TypeScript strict) |
| 스타일링 | Tailwind CSS v4 |
| 컨테이너 | Docker / Docker Compose |
| 배포 — 백엔드 | Railway |
| 배포 — 프론트엔드 | Vercel |

---

## 빠른 시작

### 사전 요구사항

**Docker 사용 (권장)**
- Docker Desktop (PostgreSQL·Redis·백엔드·프론트엔드 포함)
- Anthropic API 키 (console.anthropic.com에서 발급)

**로컬 직접 실행**
- Python 3.12+
- Node.js 20+
- PostgreSQL 17+
- Redis 7+
- Anthropic API 키

### Docker Compose (권장)

```bash
# 루트 .env 파일 생성 (backend/.env.example 참고)
cp backend/.env.example .env
# .env에서 ANTHROPIC_API_KEY, ADMIN_TOKEN 설정

# 전체 스택 빌드 및 기동 (postgres, redis, backend, frontend)
docker compose up -d --build

# 중지
docker compose down
```

- 프론트엔드: http://localhost:3000
- 백엔드 API 문서: http://localhost:8000/docs

### 백엔드 (로컬 직접 실행)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

cp .env.example .env
# .env 파일에서 DATABASE_URL, ANTHROPIC_API_KEY, ADMIN_TOKEN 설정

uvicorn app.main:app --reload --port 8000
```

서버 기동 시 `create_tables()`가 자동으로 테이블(FTS 인덱스·트리거 포함)을 생성한다.

API 문서: http://localhost:8000/docs

### 프론트엔드 (로컬 직접 실행)

```bash
cd frontend
npm install

# .env.local 없으면 기본값 http://localhost:8000 사용
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev
```

프론트엔드: http://localhost:3000

---

## 프로젝트 구조

```
ai-tech-tracker/
├── backend/
│   ├── app/
│   │   ├── config.py               — 환경변수 (pydantic-settings)
│   │   ├── database.py             — 비동기 DB 세션 팩토리 + create_tables()
│   │   ├── cache.py                — Redis 헬퍼 (cache_get / cache_set)
│   │   ├── models/tech.py          — TechItem, CrawlLog, ReviewQueue
│   │   ├── routers/
│   │   │   ├── tech.py             — 공개 API (/api/tech, /api/categories 등)
│   │   │   └── admin.py            — 관리자 API (/api/admin/*)
│   │   ├── schemas/tech.py         — Pydantic 요청/응답 스키마
│   │   ├── services/
│   │   │   ├── crawler.py          — RSS + GitHub 수집 파이프라인
│   │   │   ├── ai_processor.py     — Claude API 분류·요약 (배치 + 프롬프트 캐싱)
│   │   │   └── scheduler.py        — APScheduler (매일 18:00 UTC)
│   │   └── utils/
│   │       └── deprecated_detector.py — 휴리스틱 deprecated 키워드 감지
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── Dockerfile                  — multi-stage 빌드 (standalone 출력)
│   └── src/
│       ├── app/                    — Next.js App Router 페이지
│       │   ├── page.tsx            — 메인 피드 (패치 그룹화, 필터 바)
│       │   ├── category/[slug]/    — 카테고리별 목록 (설명 헤더)
│       │   ├── tech/[id]/          — 기술 상세 (raw_content 접기, siblings)
│       │   ├── deprecated/         — deprecated 목록
│       │   ├── search/             — 검색 결과 (FTS 기반)
│       │   ├── compare/            — 기술 비교 (/compare?a=ID&b=ID)
│       │   └── admin/              — 관리자 ("use client")
│       ├── components/
│       │   ├── TechCard.tsx
│       │   ├── TechGroupCard.tsx   — 패치 버전 그룹 카드
│       │   ├── PatchVersionViewer.tsx — 버전 선택기 (클라이언트)
│       │   ├── StatusBadge.tsx
│       │   ├── DeprecatedBanner.tsx
│       │   ├── SearchBar.tsx       — 자동완성 포함 ("use client")
│       │   ├── CategoryNav.tsx     — deprecated 배지 포함
│       │   ├── FilterBar.tsx       — 상태·기간 필터 ("use client")
│       │   ├── Pagination.tsx      — 페이지네이션 UI
│       │   ├── Timeline.tsx
│       │   ├── ThemeToggle.tsx     — 다크/라이트 전환 ("use client")
│       │   └── ThemeProviderWrapper.tsx — next-themes Provider
│       └── lib/
│           ├── api.ts              — fetch 래퍼 (SSR/CSR URL 분기)
│           └── types.ts            — TechItem, Category, Status 타입 + CATEGORY_META
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   └── LEARNING.md
├── REQUIREMENTS.md                 — 기능 백로그 + 현황
└── docker-compose.yml
```

---

## 환경변수

`backend/.env.example`을 복사해 `backend/.env`를 생성한다.

| 키 | 설명 | 예시 |
|----|------|------|
| `DATABASE_URL` | PostgreSQL 연결 URL (asyncpg) | `postgresql+asyncpg://postgres:password@localhost:5432/ai_tech_tracker` |
| `REDIS_URL` | Redis 연결 URL | `redis://localhost:6379/0` |
| `ANTHROPIC_API_KEY` | Claude API 키 | `sk-ant-api03-...` |
| `GITHUB_TOKEN` | GitHub PAT (선택 — 없으면 rate limit 낮음) | `ghp_...` |
| `ADMIN_TOKEN` | 관리자 API 인증 토큰 | 임의의 긴 문자열 |
| `CORS_ORIGINS` | 허용 CORS 오리진 (쉼표 구분) | `http://localhost:3000` |
| `ENV` | 실행 환경 | `development` / `production` |

---

## 관련 문서

- [아키텍처](docs/ARCHITECTURE.md) — 시스템 구조, 데이터 흐름, DB 설계
- [개발 가이드](docs/DEVELOPMENT.md) — 로컬 환경 세팅, 컨벤션, 배포
- [기능 백로그](REQUIREMENTS.md) — 구현 현황, 우선순위 작업 목록
- [학습 노트](docs/LEARNING.md) — 기술스택 선택 이유, 설계 결정 기록

---

## 라이선스

MIT License © 2026
