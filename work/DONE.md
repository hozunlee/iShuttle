# iShuttle — 완료 작업 로그

> 완료된 태스크를 역순(최신 상단)으로 기록한다.

---

## BE_002 + FE_002 | TDD 기반 테스트 스위트 구축

> 완료: 2026-03-23
> 담당: BE + FE

### 작업 내용

**신규 구현**
- `backend/pipeline/game_rules.py` — check_winner / check_court_change (CONTEXT.md 룰 완전 구현)
- `frontend/src/utils/rally.ts` — scoreRally / getTop3Rallies / calcPhase
- `frontend/` vitest 설정 (package.json, vite.config.ts)

**테스트 파일**
- `backend/tests/test_game_rules.py` — 23개 (check_winner 듀스/cap/일반 전 케이스, check_court_change)
- `backend/tests/test_api.py` — 25개 (health, analyze, status, results, feedback 전 엔드포인트)
- `backend/tests/test_pose_calc.py` — 17개 (수학 함수 경계값: 수평/수직/45도/안전처리)
- `backend/tests/test_reporter.py` — 21개 (template 구조, API키 없음, JSON 파싱)
- `backend/tests/test_pipeline.py` 확장 — 엣지케이스 추가 (neutral 결과, 빈 배열, gap 경계값)
- `frontend/src/__tests__/gameStore.test.ts` — 12개
- `frontend/src/__tests__/jobStore.test.ts` — 19개
- `frontend/src/__tests__/scoreRally.test.ts` — 15개

### 최종 결과

- Backend: **112 / 112 passed**
- Frontend: **46 / 46 passed**

---

## BE_001 | 백엔드 스캐폴딩

> 완료: 2026-03-23
> 담당: BE

### 작업 내용

- `backend/main.py` — FastAPI 앱, CORS, StaticFiles, WebSocket
- `backend/api/` — analyze.py / results.py / feedback.py
- `backend/pipeline/__init__.py` — 6단계 순차 파이프라인
- `backend/pipeline/` — court.py / tracker.py / rally.py / editor.py / formation.py / pose.py / reporter.py
- `backend/pyproject.toml` — uv 패키지 설정

### 주요 결정

- Claude 모델명: claude-sonnet-4-6 (Spec.md의 claude-sonnet-4-20250514 아님)
- result enum: "us" | "them" | "neutral" (CONTEXT.md 기준)
- OOM 방지: 6단계 순차 실행, 각 모델 사용 후 즉시 해제

---

## FE_001 | 프론트엔드 스캐폴딩

> 완료: 2026-03-23
> 담당: FE

### 작업 내용

- React + TypeScript + Vite + Tailwind + Zustand 기본 구조
- pages/: Setup / Analyzing / Results / RallyView / HeatmapView / ReportView
- components/: VideoUploader / ProgressBar / RallyCard / HeatmapViewer / AIReport
- store/: gameStore / jobStore
- api/: client / analyze / results / feedback + mock.ts
- `VITE_USE_MOCK=true` 환경변수로 Mock API 제어

### 주요 결정

- SPEC.md 타입 불일치 수정 (CONTEXT.md 기준): result, clip_url, heatmap_url, deuce_trigger+cap
