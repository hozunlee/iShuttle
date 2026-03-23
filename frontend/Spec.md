# iShuttle Frontend — 기술 요강

> frontend/SPEC.md | React UI 전담
> CONTEXT.md를 먼저 읽고 이 파일을 읽어라

---

## 환경

```bash
pnpm create vite ishuttle-ui -- --template react-ts
cd ishuttle-ui
pnpm install
pnpm add zustand axios react-router-dom
pnpm add -D tailwindcss @types/react
pnpm dev   # :5173
```

**Node:** 20+
**패키지 매니저:** pnpm (npm/yarn 사용 금지)
**언어:** TypeScript

---

## 폴더 구조

```
frontend/
├── SPEC.md
├── package.json
├── vite.config.ts
├── tailwind.config.ts
└── src/
    ├── main.tsx
    ├── App.tsx              # 라우터 정의
    ├── api/
    │   ├── client.ts        # axios 인스턴스 (baseURL: localhost:8000)
    │   ├── analyze.ts       # POST /api/analyze
    │   ├── results.ts       # GET /api/results
    │   └── feedback.ts      # POST /api/feedback
    ├── store/
    │   ├── gameStore.ts     # 게임 설정 상태 (zustand)
    │   └── jobStore.ts      # 분석 job 상태 (zustand)
    ├── pages/
    │   ├── Setup.tsx        # / 게임 설정 + 업로드
    │   ├── Analyzing.tsx    # /analyzing/:jobId 진행률
    │   ├── Results.tsx      # /results/:jobId 결과 허브
    │   ├── RallyView.tsx    # /results/:jobId/rallies 랠리 클립
    │   ├── HeatmapView.tsx  # /results/:jobId/heatmap 히트맵
    │   └── ReportView.tsx   # /results/:jobId/report AI 리포트
    ├── components/
    │   ├── UploadZone.tsx   # 드래그앤드롭 업로드
    │   ├── ProgressBar.tsx  # 실시간 진행률
    │   ├── RallyCard.tsx    # 랠리 클립 카드
    │   ├── Heatmap.tsx      # 히트맵 시각화
    │   └── ReportCard.tsx   # AI 리포트 카드
    └── types/
        └── api.ts           # RallyReport 등 API 타입 정의
```

---

## 라우트 구조

```
/                        게임 설정 + 영상 업로드
/analyzing/:jobId        분석 진행률 (WebSocket 실시간)
/results/:jobId          결과 허브 (탭 네비게이션)
  /results/:jobId/rallies     랠리 클립 뷰
  /results/:jobId/heatmap     포지션 히트맵
  /results/:jobId/report      AI 게임 리포트
```

---

## 타입 정의 (api.ts)

```typescript
// CONTEXT.md의 RallyReport JSON 스키마와 1:1 대응
export interface GameRule {
    mode: "amateur" | "bwf_21";
    win_score: number;
    deuce_score: number;
    court_change_at: number;
}

export interface Rally {
    id: number;
    timestamp: { start_sec: number; end_sec: number };
    strokes: number;
    result: "우리팀_득점" | "상대팀_득점";
    score_at_end: { us: number; them: number };
    phase: "phase1" | "phase2" | "phase3" | "deuce";
    formation: {
        dominant: "front_back" | "side_by_side" | "transition";
        transitions: number;
    };
    clip_path: string;
    short_path: string;
}

export interface PoseSummary {
    shoulder_rotation_avg: number;
    spine_tilt_avg: number;
    knee_bend_avg: number;
    confidence: "high" | "medium" | "low";
}

export interface AIReport {
    summary: string;
    pros: string;
    cons: string[];
    focus: string;
}

export interface RallyReport {
    game_id: string;
    rule: GameRule;
    score: { us: number; them: number };
    rallies: Rally[];
    heatmap_path: string;
    pose_summary: PoseSummary;
    ai_report: AIReport;
}

export interface JobStatus {
    progress: number; // 0~100
    step: string;
}
```

---

## 상태 관리 (Zustand)

```typescript
// store/gameStore.ts
interface GameConfig {
    my_player: "A1" | "A2";
    partner: "A1" | "A2";
    rule_mode: "amateur" | "bwf_21";
    video_path: string | null;
}

// store/jobStore.ts
interface JobState {
    job_id: string | null;
    progress: number;
    step: string;
    status: "idle" | "processing" | "done" | "error";
    result: RallyReport | null;
}
```

---

## API 호출 패턴

```typescript
// api/client.ts
import axios from "axios";
export const api = axios.create({ baseURL: "http://localhost:8000" });

// WebSocket 진행률 구독
export function subscribeProgress(
    jobId: string,
    onUpdate: (s: JobStatus) => void,
) {
    const ws = new WebSocket(`ws://localhost:8000/ws/progress/${jobId}`);
    ws.onmessage = (e) => onUpdate(JSON.parse(e.data));
    return () => ws.close(); // cleanup 함수 반환
}
```

---

## Mock API (BE 연동 전 독립 개발용)

```typescript
// api/mock.ts — BE 완성 전 FE 개발에 사용
export const mockAnalyze = async () => ({
    job_id: "mock-001",
    status: "processing",
});

export const mockProgress: JobStatus[] = [
    { progress: 10, step: "코트 라인 감지 중..." },
    { progress: 30, step: "선수 추적 중..." },
    { progress: 55, step: "랠리 분리 중..." },
    { progress: 80, step: "자세 분석 중..." },
    { progress: 95, step: "AI 리포트 생성 중..." },
    { progress: 100, step: "완료" },
];
```

---

## 코딩 규칙

- 컴포넌트당 1 책임. 200줄 넘으면 분리
- 상태관리는 zustand만. useState는 로컬 UI 상태(열림/닫힘 등)만 허용
- API 타입은 `types/api.ts`에서만 정의. 인라인 타입 금지
- BE 연동 전에는 mock.ts 사용. 실제 연동 시 mock import 제거
- CORS 설정은 BE가 담당. FE에서 proxy 설정 금지
- 영상 파일은 경로(string)만 전달. 파일 자체를 상태에 저장 금지 (메모리)
- 에러 처리: 모든 API 호출에 try/catch + 사용자 안내 toast
