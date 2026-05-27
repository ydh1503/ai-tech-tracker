# 개발 가이드

---

## 개발 환경 요구사항

| 도구 | 버전 | 용도 |
|------|------|------|
| Python | 3.12+ | 백엔드, 크롤러, AI 처리 |
| Node.js | 22+ | 프론트엔드 (Docker: node:22-alpine) |
| npm | 10+ | 패키지 관리 |
| PostgreSQL | 17+ | 주 데이터베이스 (Docker: postgres:17-alpine) |
| Redis | 7+ | 캐시 (Docker: redis:7-alpine) |
| Docker Desktop | 4+ | 전체 스택 컨테이너 실행 |
| Git | 2.40+ | 버전 관리 |

---

## 로컬 환경 세팅

### 1. 저장소 클론

```bash
git clone https://github.com/<your-username>/ai-tech-tracker.git
cd ai-tech-tracker
```

### 2. Docker Compose (권장)

```bash
# 루트 .env 파일 생성
cp backend/.env.example .env
# .env에서 ANTHROPIC_API_KEY, ADMIN_TOKEN 설정 (필수)

# 전체 스택 빌드 (postgres:17-alpine + redis:7-alpine + backend + frontend)
docker compose up -d --build

# 로그 확인
docker compose logs -f backend
docker compose logs -f frontend

# 중지
docker compose down
```

> SSR/CSR URL 분기: 컨테이너 내부에서 백엔드 호출은 `BACKEND_URL=http://backend:8000`,
> 브라우저 클라이언트는 `NEXT_PUBLIC_API_URL=http://localhost:8000` 사용.

### 3. 백엔드 세팅

```bash
cd backend

python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

cp .env.example .env
# .env 파일을 열어 아래 항목 입력:
# DATABASE_URL, ANTHROPIC_API_KEY, ADMIN_TOKEN (필수)
# REDIS_URL, GITHUB_TOKEN, CORS_ORIGINS (선택)
```

### 3. 데이터베이스 초기화

```bash
# PostgreSQL이 실행 중인지 확인 후 DB 생성
createdb ai_tech_tracker

# 별도 마이그레이션 불필요 — 서버 기동 시 create_tables()가 자동으로 테이블 생성
uvicorn app.main:app --reload --port 8000
# 로그에서 "DB 테이블 생성/확인 완료" 확인
```

> **주의**: 현재 Alembic 마이그레이션이 미적용 상태입니다. 스키마를 변경하면 기존 테이블을 직접 drop하거나 ALTER TABLE을 수동 실행해야 합니다.
> Alembic 도입 방법은 [백로그 P1-1](../REQUIREMENTS.md)을 참고하세요.

### 4. 백엔드 실행

```bash
# backend/ 디렉토리에서
uvicorn app.main:app --reload --port 8000
```

API 문서: http://localhost:8000/docs

### 5. 프론트엔드 세팅 및 실행

```bash
cd frontend
npm install

# .env.local 없으면 http://localhost:8000이 기본값으로 사용됨
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev
```

프론트엔드: http://localhost:3000

---

## 크롤링 수동 실행

서버 실행 중 크롤링을 즉시 트리거하는 방법:

```bash
# ADMIN_TOKEN은 .env의 ADMIN_TOKEN 값
curl -X POST http://localhost:8000/api/admin/crawl/trigger \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# 응답: {"message": "크롤링이 백그라운드에서 시작되었습니다."}
# 크롤링은 비동기 실행 — 완료 여부는 로그 또는 /api/admin/crawl/logs로 확인
```

```bash
# 크롤링 로그 확인
curl http://localhost:8000/api/admin/crawl/logs \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

---

## 코드 컨벤션

### Python (백엔드)

```bash
# 포매터
black .

# 린터
ruff check .
ruff check --fix .

# 타입 체크
mypy app/
```

- 파일명: `snake_case.py`
- 클래스명: `PascalCase`
- 함수/변수명: `snake_case`
- 비동기 I/O는 반드시 `async def` + `await`

### TypeScript (프론트엔드)

```bash
npm run lint
npm run type-check
```

- `any` 타입 금지 (`tsconfig.json` `strict: true`)
- 서버 컴포넌트 기본 — 클라이언트 상태가 필요한 경우만 `"use client"` 선언
- 컴포넌트 파일명: `PascalCase.tsx`
- 유틸리티 파일명: `camelCase.ts`

---

## 테스트

### 백엔드 (pytest)

```bash
cd backend
pytest
pytest -v
pytest --cov=app --cov-report=html
```

테스트 파일: `backend/tests/test_*.py`

### 프론트엔드 (Jest)

```bash
cd frontend
npm test
npm run test:ci    # CI용 단회 실행
```

테스트 파일: `src/**/*.test.tsx` 또는 `src/**/__tests__/`

---

## 브랜치 전략

| 브랜치 | 설명 |
|--------|------|
| `main` | 배포 가능한 안정 버전 |
| `develop` | 통합 개발 브랜치 |
| `feature/기능명` | 새 기능 (예: `feature/cache-invalidation`) |
| `fix/버그명` | 버그 수정 (예: `fix/admin-commit-missing`) |

PR 규칙: `feature/*` → `develop` → 리뷰 → 병합. `develop` → `main`은 배포 준비 시.

---

## 커밋 메시지 규칙

형식: `type: 한국어 설명`

| 타입 | 사용 시점 |
|------|----------|
| `feat` | 새 기능 추가 |
| `fix` | 버그 수정 |
| `update` | 기존 기능 개선·변경 |
| `docs` | 문서 수정 |
| `refactor` | 기능 변경 없는 구조 개선 |
| `test` | 테스트 추가·수정 |
| `chore` | 빌드·의존성·설정 변경 |

예시:
- `feat: 크롤러 실행 후 Redis 캐시 무효화 추가`
- `fix: admin 라우터 commit 누락 수정`
- `update: RSS 소스에 Anthropic 공식 블로그 추가`
- `chore: alembic 마이그레이션 초기 설정`

---

## 배포

### 백엔드 — Railway

1. Railway 프로젝트 생성 후 GitHub 저장소 연결
2. Root Directory: `backend`
3. 환경변수를 Railway 대시보드에서 설정 (`DATABASE_URL`, `ANTHROPIC_API_KEY`, `ADMIN_TOKEN` 등)
4. `main` 브랜치 푸시 시 자동 배포

Railway에서 PostgreSQL, Redis 서비스도 함께 생성 가능 (`DATABASE_URL`, `REDIS_URL` 자동 주입).

### 프론트엔드 — Vercel

1. Vercel 프로젝트 생성 후 GitHub 저장소 연결
2. Root Directory: `frontend`
3. `NEXT_PUBLIC_API_URL`을 프로덕션 Railway URL로 설정
4. `main` 브랜치 푸시 시 자동 배포

---

## 알려진 이슈 및 해결 방법

### `asyncpg.InvalidCatalogNameError: database "ai_tech_tracker" does not exist`

PostgreSQL에 DB가 없는 경우.

```bash
createdb ai_tech_tracker
```

### `ANTHROPIC_API_KEY is required` 오류

`backend/.env`에 `ANTHROPIC_API_KEY` 값 미설정.

```bash
# .env.example 참고하여 키 설정
# ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Next.js fetch에서 `ECONNREFUSED` 오류

백엔드 서버가 실행 중인지 확인. http://localhost:8000/docs 접근 가능 여부 체크.

### Tailwind CSS 클래스가 적용되지 않을 때

Tailwind CSS v4는 `tailwind.config.ts`를 사용하지 않는다.
다크 모드가 적용되지 않으면 `src/styles/globals.css` 상단의 아래 설정을 확인:

```css
@custom-variant dark (&:where(.dark, .dark *));
```

`next-themes`가 `<html>` 태그에 `.dark` 클래스를 추가하므로 이 설정이 없으면 다크 모드 클래스가 무시된다.
개발 서버 재시작 후에도 적용 안 되면 `.next/` 캐시 삭제 후 재시작.

### TypeScript `Type 'any' is not assignable` 오류

`lib/api.ts`에서 반환 타입을 명시적으로 지정하고 `unknown` 사용 후 타입 가드로 좁힌다.

### 크롤링 후 카테고리/타임라인이 즉시 갱신되지 않을 때

크롤러 완료 시 `cache_delete("categories")`, `cache_delete("timeline")`이 자동 호출된다.
수동으로 삭제해야 할 경우:

```bash
redis-cli DEL categories timeline
```

### admin API에서 변경사항이 반영되지 않을 때

현재 admin 라우터에서 `await db.flush()` 후 명시적 `commit()`이 없는 경우가 있음.
`get_db` 의존성의 `commit()`에 의존하므로 요청 완료 시 자동 커밋됨.
만약 변경이 반영되지 않는다면 `database.py`의 `get_db()` 함수의 트랜잭션 스코프를 확인하세요.
