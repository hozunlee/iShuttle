# iShuttle — 전체 기술 기획

> v2.5 | 2026-03-22 | 코딩 세션 시작 전 반드시 읽을 것

---

## 브랜드

**iShuttle** (아이셔틀) — 표기는 항상 소문자 `i` 고수

| 레이어     | 의미                                                      |
| ---------- | --------------------------------------------------------- |
| **i**      | 소문자 고수 — Apple 제품군(iPhone, iPad) 네이밍 관습 차용 |
| **eye**    | 눈(目) — AI가 영상을 대신 분석한다는 기능적 메타포        |
| **아이셔** | 아이셔 캔디 브랜드 — 발음 동일, 친숙함·접근성 확보        |

**슬로건:** _"눈으로 다시 보는 나의 배드민턴"_
**UI 원칙:** 기능 진입 단계 최소화. 업로드 → 결과까지 3탭 이내.

---

## 제품 정의

> 동호인이 스마트폰으로 촬영한 배드민턴 복식 게임 영상을
> AI 파이프라인이 자동 분석해 랠리 클립·숏폼·포메이션 데이터·자세 수치·텍스트 리포트를 생성하는 로컬 실행 웹앱

- **타겟:** 주 1회 이상 배드민턴 복식을 즐기는 동호인 (20~30대 중심)
- **촬영 조건:** 코트 후방 중앙, 삼각대 고정, 높이 1.5~2m, 1080p/30fps 이상
- **실행 환경:** 로컬 PC (RAM 16GB+, GPU 선택), 브라우저에서 localhost:5173 접속
- **네트워크:** 로컬 전용. Claude API 호출 시에만 외부 연결 필요

---

## 목표 5단계

| #   | 사용자 행동                                         | 측정 기준                                    | 담당 기능 |
| --- | --------------------------------------------------- | -------------------------------------------- | --------- |
| 1   | **본다** — 20분 영상에서 핵심 랠리 클립만 재생      | 랠리 클립 수 ≥ 20개 / 클립 평균 재생률 ≥ 80% | F1        |
| 2   | **공유한다** — 9:16 숏폼을 SNS에 업로드             | 숏폼 파일 다운로드 완료                      | F2        |
| 3   | **이해한다** — 히트맵·포메이션으로 자신의 패턴 확인 | 히트맵 1개 + 포메이션 분류 데이터 생성       | F3        |
| 4   | **피드백받는다** — AI 리포트에서 개선점 확인        | 리포트 생성 완료 + 사용자 열람               | F4 + F5   |
| 5   | **성장한다** — 게임 간 수치 변화 추적 (v2 이후)     | 누적 게임 수 ≥ 3개 기준 지표 변화 표시       | v2        |

---

## 핵심기능 5개 (MVP)

| 기능                  | 설명                                                                                                                                                                            | 담당  |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| F1. 스마트 랠리 추출  | TrackNetV3 셔틀콕 추적 → 랠리 자동 분리. 화각 이탈 시 선형 보간(최대 30프레임). 초과 시 랠리 종료 처리. 타임스탬프 JSON + MP4 클립 저장                                         | BE    |
| F2. 숏폼 자동 편집    | TOP3 랠리 선정¹, 9:16 크롭, 슬로우모션², 텍스트 오버레이 (점수·랠리 번호), BGM 삽입                                                                                             | BE    |
| F3. 포지션 & 포메이션 | YOLOv8n-pose + ByteTrack 선수 4명 추적, 코트 9구역 히트맵, 전후/좌우/과도기 포메이션 분류                                                                                       | BE    |
| F4. 자세 분석         | MediaPipe Pose 2D 키포인트 (model_complexity=1). 등쪽 촬영 기준 어깨 회전각·척추 기울기·무릎 굽힘·스탠스 너비 수치화. visibility < 0.5 프레임은 해당 관절을 confidence=low 처리 | BE    |
| F5. AI 게임 리포트    | 게임 종료 후 전체 RallyReport를 Claude API에 1회 전송³. 출력: 총평 1문단 / 잘한점 1개 / 개선점 2개 / 다음 게임 집중포인트 1개                                                   | BE→FE |

> ¹ **TOP3 선정 공식**
>
> ```python
> def score_rally(r):
>     return r["strokes"] * 2 + (10 if r["result"] == "us" else 0)
> top3 = sorted(rallies, key=score_rally, reverse=True)[:3]
> ```
>
> 모든 랠리 대상. 타수(strokes)에 ×2 가중치.
> 우리팀 득점(result == "us") 시 +10 보너스.

> ² **슬로우모션 구현 전략**
>
> | 레벨           | 조건                                               | 처리 방식                                              |
> | -------------- | -------------------------------------------------- | ------------------------------------------------------ |
> | Level 2 (기본) | TrackNetV3 속도벡터 급변점으로 타격 시점 감지 성공 | 타격 시점 기준 -1s~+0.5s 구간만 FFmpeg setpts=2.0\*PTS |
> | Level 1 (폴백) | 타격 시점 감지 실패                                | 클립 전체 FFmpeg setpts=2.0\*PTS 0.5배속               |
> | 제외           | AI 프레임 보간 (RIFE 등) — GPU 필수                | MVP 미구현                                             |
>
> 다운로드 파일: FFmpeg 인코딩. 브라우저 미리보기: video.playbackRate = 0.5.

> ³ **F5 Claude API 선택 기준**
>
> | 항목            | 값                                                     |
> | --------------- | ------------------------------------------------------ |
> | 모델            | claude-sonnet-4-6                                      |
> | 컨텍스트 윈도우 | 200K 토큰                                              |
> | 인증            | ANTHROPIC_API_KEY 환경변수                             |
> | 폴백            | 키 없거나 HTTP 오류 시 룰 기반 템플릿 리포트 자동 생성 |

---

## 아키텍처

```
[사용자 브라우저]
      ↕ HTTP / WebSocket
[React + Vite]  :5173                   ← frontend/
      ↕ REST API (Vite proxy → :8000)
[FastAPI]        :8000                  ← backend/
  ├─ /static  → output/                ← StaticFiles 마운트
  ├─ BackgroundTasks                   ← AI 파이프라인 비동기 실행
  └─ jobs: dict[job_id, JobState]      ← 인메모리 진행 상태
      ↕ subprocess
[AI Pipeline]                          ← backend/pipeline/ (순차 Load/Unload)
      ↓
[output/]                              ← 런타임 결과물 (gitignore)
    ├── clips/
    ├── shorts/
    └── heatmap/
```

**정적 파일 마운트:**

```python
app.mount("/static", StaticFiles(directory="output"), name="static")
# 접근: http://localhost:8000/static/clips/rally_001.mp4
```

**비동기 처리:**

- `BackgroundTasks`로 파이프라인 실행. Celery·Redis 미사용.
- job 상태: 인메모리 dict — `{ job_id: { "progress": 42, "step": "rally_detection" } }`
- 서버 재시작 시 진행 중 작업 유실. 로컬 단일 유저 환경에서 허용.

---

## AI 파이프라인 — 셔틀콕 화각 이탈 처리

배드민턴 클리어·로브 샷에서 셔틀콕이 카메라 화각 상단을 벗어날 수 있다.
랠리 종료로 잘못 판정하지 않도록 아래 규칙을 적용한다.

### 이탈 유형 분류

| 유형          | 판정 조건                                | 처리                                |
| ------------- | ---------------------------------------- | ----------------------------------- |
| **임시 이탈** | 수직 방향 이탈 + 미감지 연속 ≤ 30프레임  | 직전·직후 위치 선형 보간, 추적 유지 |
| **아웃 이탈** | 수평 경계 이탈 + 속도벡터 코트 외부 방향 | 해당 프레임을 end_sec으로 마킹      |
| **타임아웃**  | 미감지 연속 > 30프레임 (= 1초 @ 30fps)   | 랠리 종료 처리                      |

### 보간 함수 시그니처

```python
def interpolate_positions(
    positions: list[tuple[int, float, float, float]],  # (frame, x, y, conf)
    max_gap: int = 30
) -> list[tuple[int, float, float, float]]:
    """
    conf == 0 구간을 직전·직후 위치로 선형 보간.
    연속 미감지가 max_gap 초과 시 보간 중단 → 호출자가 랠리 종료 처리.
    """
```

### 서브 준비 동작 구분

서브 전 셔틀 토스를 랠리 시작으로 오인 방지:

- 셔틀 최초 감지 후 30프레임 이내에 속도 > HIT_SPEED_THRESHOLD 미충족 시 → 서브 준비 상태 유지
- 조건 충족 시점을 start_sec으로 마킹

### detection_gaps 필드

```json
"detection_gaps": [
  { "start_frame": 450, "end_frame": 478, "interpolated": true },
  { "start_frame": 512, "end_frame": 560, "interpolated": false }
]
```

`interpolated: false` = 보간 한계 초과, 해당 구간 데이터 없음.

---

## API 계약 (프론트-백 인터페이스)

> 스키마 변경 시 work/API_CHANGES.md에 이력을 먼저 남기고 이 파일을 수정한다

### 엔드포인트

```
POST  /api/analyze
      multipart/form-data: { video_file: UploadFile, game_config: str(JSON) }
      → { job_id: str, status: "processing" }

GET   /api/status/{job_id}
      → { progress: int(0~100), step: str }

GET   /api/results/{job_id}
      → RallyReport JSON

POST  /api/feedback
      body: { game_id: str, rally_ids: int[] }
      → { summary: str, pros: str, cons: str[], focus: str }

WS    /ws/progress/{job_id}
      → { progress: int, step: str }  (실시간 push)
```

> `/api/clip`, `/api/short` 엔드포인트 없음. 정적 파일은 `/static/...` 직접 접근.

### Enum 허용값

```
result             : "us" | "them" | "neutral"

phase              : "phase1"  → 양팀 합산 리드 점수 기준 0~8점 구간
                   | "phase2"  → 9~17점
                   | "phase3"  → 18~24점 (양팀 중 한 쪽이 24점 도달 전까지)
                   | "deuce"   → 양팀 모두 24점 이상 (듀스 진행 중)

formation.dominant : "front_back" | "side_by_side" | "transition"

confidence         : "high" | "medium" | "low"
```

### RallyReport JSON 스키마

```json
{
    "game_id": "uuid-v4",
    "rule": {
        "mode": "amateur",
        "win_score": 25,
        "deuce_trigger": 24,
        "deuce_cap": 31,
        "court_change_at": 13
    },
    "score": { "us": 25, "them": 18 },
    "rallies": [
        {
            "id": 1,
            "timestamp": { "start_sec": 12.4, "end_sec": 21.7 },
            "strokes": 9,
            "result": "us",
            "score_at_end": { "us": 1, "them": 0 },
            "phase": "phase1",
            "formation": { "dominant": "front_back", "transitions": 2 },
            "clip_url": "/static/clips/rally_001.mp4",
            "short_url": "/static/shorts/rally_001_916.mp4",
            "detection_gaps": [
                { "start_frame": 450, "end_frame": 478, "interpolated": true }
            ]
        }
    ],
    "heatmap_url": "/static/heatmap/{game_id}.png",
    "pose_summary": {
        "shoulder_rotation_avg": 48.2,
        "spine_tilt_avg": 19.3,
        "knee_bend_avg": 128.5,
        "confidence": "high"
    },
    "ai_report": {
        "summary": "string",
        "pros": "string",
        "cons": ["string", "string"],
        "focus": "string"
    }
}
```

---

## 게임 룰 (동호인 단판승부)

```python
# 단판, 25점 선취 / 24-24 → 듀스, 2점차 선승 / 31점 즉시 종료
GAME_MODE = {
    "amateur": {
        "win_score":       25,
        "deuce_trigger":   24,   # 양팀 모두 24점 도달 시 듀스 진입
        "deuce_win_diff":   2,   # 듀스 중 2점 차 달성 시 승리
        "deuce_cap":       31,   # 31점 도달 즉시 승리 (듀스 상한)
        "court_change_at": 13,   # 13점 도달 시 코트교체 (1회)
        "sets":             1,
    }
}

def check_winner(us: int, them: int, mode: str = "amateur") -> str | None:
    """반환: 'us' | 'them' | None(경기 계속)"""
    m = GAME_MODE[mode]
    if us >= m["deuce_cap"] or them >= m["deuce_cap"]:
        return "us" if us > them else "them"
    if us >= m["deuce_trigger"] and them >= m["deuce_trigger"]:
        if abs(us - them) >= m["deuce_win_diff"]:
            return "us" if us > them else "them"
        return None
    if us >= m["win_score"]: return "us"
    if them >= m["win_score"]: return "them"
    return None

def check_court_change(us: int, them: int, mode: str = "amateur") -> bool:
    """13점 정확히 도달한 순간 True. 이후 재호출 방지는 호출자 책임."""
    t = GAME_MODE[mode]["court_change_at"]
    return us == t or them == t
```

---

## 파이프라인 실행 순서 (OOM 방지 — 순차 Load/Unload)

> 모델 동시 적재 금지. 각 단계 종료 후 즉시 메모리 해제.

| 단계          | 모듈        | 사용 모델               | 피크 메모리 | 해제 방법       |
| ------------- | ----------- | ----------------------- | ----------- | --------------- |
| ① 코트 감지   | court.py    | OpenCV (모델 없음)      | ~50MB       | —               |
| ② 선수 추적   | tracker.py  | YOLOv8n-pose            | ~200MB      | `del model`     |
| ③ 셔틀콕 추적 | rally.py    | TrackNetV3 (subprocess) | ~100MB      | 프로세스 종료   |
| ④ 클립 편집   | editor.py   | FFmpeg (모델 없음)      | ~100MB      | —               |
| ⑤ 자세 분석   | pose.py     | MediaPipe Pose          | ~100MB      | `model.close()` |
| ⑥ 리포트 생성 | reporter.py | Claude API (외부 HTTP)  | ~10MB       | —               |

단계별 피크 메모리: 최대 ~200MB. 동시 적재 시 합산 ~560MB.
RAM 16GB 환경에서 순차 실행 시 OOM 발생 조건 해당 없음.

---

## 리스크 요약

| 리스크                         | 심각도 | 감지 조건                                     | 대응                                                     |
| ------------------------------ | ------ | --------------------------------------------- | -------------------------------------------------------- |
| 셔틀콕 미감지 (저조도·역광)    | 중     | TrackNetV3 confidence < 0.3 연속 5프레임 이상 | OpenCV 광학 플로우 폴백 → 실패 시 수동 랠리 지정 UI      |
| 셔틀콕 화각 이탈 (클리어·로브) | 중     | 미감지 연속 1프레임 이상                      | 선형 보간 최대 30프레임. 초과 시 랠리 종료 마킹          |
| 선수 ID 스왑 (교차 순간)       | 중     | ByteTrack ID 불연속                           | 게임 설정 시 팀 색상·위치 앵커 지정으로 초기 ID 고정     |
| 코트교체 감지 실패             | 중     | 13점 이후 선수 좌표 역전 미감지               | 13점 도달 시 사용자 확인 팝업 + 수동 토글                |
| MediaPipe 3D depth 왜곡        | 낮음   | model_complexity ≥ 2 사용                     | 2D 키포인트 전용. complexity=1 고정                      |
| CPU only 처리 속도 저하        | 중     | GPU 미탑재                                    | 720p 다운샘플링. TensorRT INT8 적용 가능 시 적용         |
| 앞 선수 자세 사각지대          | 중     | MediaPipe visibility < 0.5                    | 해당 관절 confidence=low 처리. 리포트에서 해당 수치 제외 |
| Claude API 연결 실패           | 중     | ANTHROPIC_API_KEY 미설정 또는 HTTP 오류       | 룰 기반 템플릿 리포트 자동 폴백                          |
| RAM OOM — 모델 동시 적재       | 상     | 메모리 사용량 > 8GB                           | 6단계 순차 실행 강제. 단계별 Load/Unload. 피크 ~200MB    |

---

## 폴더 구조

```
ishuttle/
├── CONTEXT.md
├── work/
│   ├── WORKFLOW.md
│   ├── API_CHANGES.md
│   ├── DONE.md
│   └── tasks/
├── backend/
│   ├── SPEC.md
│   └── ...
├── frontend/
│   ├── SPEC.md
│   └── ...
└── output/                 ← gitignore
    ├── clips/
    ├── shorts/
    └── heatmap/
```

---

_서비스명은 iShuttle (아이셔틀). 소문자 i 고수. ShuttleIQ 표기 금지._
