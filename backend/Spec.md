# iShuttle Backend — 기술 요강

> backend/SPEC.md | Python AI 파이프라인 전담
> CONTEXT.md를 먼저 읽고 이 파일을 읽어라

---

## 환경

```bash
# 초기 세팅
uv init ishuttle-backend && cd ishuttle-backend
uv add fastapi uvicorn ultralytics mediapipe anthropic \
        moviepy ffmpeg-python opencv-python numpy pandas torch

# TrackNetV3 클론
git clone https://github.com/qaz812345/TrackNetV3.git

# 실행
uv run uvicorn main:app --reload --port 8000
```

**Python:** 3.11+
**패키지 매니저:** uv (pip 사용 금지)

---

## 폴더 구조

```
backend/
├── SPEC.md
├── pyproject.toml          # uv 의존성
├── main.py                 # FastAPI 앱 진입점
├── api/
│   ├── analyze.py          # POST /api/analyze
│   ├── results.py          # GET /api/results
│   └── feedback.py         # POST /api/feedback
├── pipeline/
│   ├── court.py            # 코트 감지 & 캘리브레이션
│   ├── tracker.py          # YOLOv8 + ByteTrack 선수 추적
│   ├── rally.py            # TrackNetV3 랠리 분리
│   ├── formation.py        # 포메이션 분류기
│   ├── pose.py             # MediaPipe 자세 분석
│   ├── editor.py           # FFmpeg 숏폼 편집
│   └── reporter.py         # Claude API 리포트 생성
├── models/
│   └── TrackNetV3/         # git submodule
└── tests/
    └── test_pipeline.py
```

---

## 파이프라인 실행 순서

```
영상 입력
  │
  ▼
court.py      코트 4꼭짓점 감지 → 호모그래피 행렬
  │
  ▼
tracker.py    YOLOv8n-pose + ByteTrack → 선수 4명 프레임별 위치
  │
  ▼
rally.py      TrackNetV3 셔틀콕 추적 → 랠리 시작/끝 타임스탬프
  │
  ├──▶ editor.py      랠리별 MP4 클립 + 9:16 숏폼 생성 (FFmpeg)
  │
  ▼
formation.py  선수 위치 → 전후/좌우/과도기 포메이션 분류
  │
  ▼
pose.py       스윙 순간 MediaPipe 자세 분석 (촬영 측 선수만)
  │
  ▼
reporter.py   모든 데이터 → Claude API → 자연어 리포트
  │
  ▼
/output/{job_id}/ 저장 → FastAPI가 FE에 서빙
```

---

## 기술별 사용 가이드

### TrackNetV3 — 셔틀콕 추적

```python
# 정확도: 97.51% (방송화질 기준, 동호인 영상 -10~15% 예상)
# 폴백: 감지 실패 시 OpenCV 광학 플로우
import subprocess
result = subprocess.run([
    "python", "models/TrackNetV3/predict.py",
    "--video_file", video_path,
    "--tracknet_file", "models/TrackNetV3/ckpts/TrackNet_best.pt",
    "--inpaintnet_file", "models/TrackNetV3/ckpts/InpaintNet_best.pt",
    "--save_dir", output_dir
])
# 출력: CSV (frame, x, y, visibility)
```

### YOLOv8 + ByteTrack — 선수 추적

```python
from ultralytics import YOLO
model = YOLO("yolov8n-pose.pt")
results = model.track(
    source=video_path,
    persist=True,
    tracker="bytetrack.yaml",
    conf=0.5,
    iou=0.5
)
# result.boxes.id: 선수 ID
# result.keypoints.xy: 33관절 2D 좌표
```

### MediaPipe Pose — 자세 분석

```python
import mediapipe as mp
mp_pose = mp.solutions.pose

# ⚠️ 규칙: model_complexity=1 고정, 3D 키포인트 사용 금지
with mp_pose.Pose(model_complexity=1, static_image_mode=False) as pose:
    results = pose.process(frame_rgb)
    if results.pose_landmarks:
        lm = results.pose_landmarks.landmark
        # 2D만 사용: lm[idx].x, lm[idx].y (정규화 좌표)
        # 후면에서 유효한 관절: 11,12(어깨) 23,24(골반) 25,26(무릎) 27,28(발목)
```

### 포메이션 분류 로직

```python
def classify_formation(p1_y, p1_x, p2_y, p2_x):
    """촬영 측 두 선수의 코트 좌표 기반 분류"""
    dy = abs(p1_y - p2_y)  # 전후 거리
    dx = abs(p1_x - p2_x)  # 좌우 거리
    if dy > dx * 1.5:
        return "front_back"      # 공격 전후
    elif dx > dy * 1.5:
        return "side_by_side"    # 수비 좌우
    else:
        return "transition"      # 과도기
```

### Claude API — 리포트 생성

```python
import anthropic
client = anthropic.Anthropic()

def generate_report(game_data: dict) -> dict:
    prompt = f"""
배드민턴 복식 동호인 게임 분석 데이터:
- 최종 스코어: {game_data['score']}
- 총 랠리: {game_data['rally_count']}개, 평균 {game_data['avg_strokes']}타
- 포메이션 비율: 전후 {game_data['formation_pct']['front_back']}%
- 실점 패턴: {game_data['loss_pattern']}
- 자세 데이터: 어깨회전 {game_data['pose']['shoulder_rotation_avg']}도

아래 형식으로 한국어 코칭 피드백을 작성해라:
1. 총평 (2문장)
2. 잘한 점 1가지
3. 개선할 점 2가지 (구체적으로)
4. 다음 게임 집중 포인트 1가지

JSON으로만 응답. 키: summary, pros, cons(배열), focus
"""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(response.content[0].text)
```

---

## FastAPI 구조

```python
# main.py
from fastapi import FastAPI, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"])

@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest, bg: BackgroundTasks):
    job_id = str(uuid4())
    bg.add_task(run_pipeline, job_id, request.video_path, request.game_config)
    return {"job_id": job_id, "status": "processing"}

@app.websocket("/ws/progress/{job_id}")
async def progress(ws: WebSocket, job_id: str):
    await ws.accept()
    # 진행률 구독 → 실시간 push
```

---

## 코딩 규칙

- 파이프라인 각 모듈(court, tracker, rally...)은 독립 실행 가능하게 작성
- 모든 AI 스텝에 `try/except` + fallback 필수
- 각 스텝 시작·완료 시 로그: `logger.info(f"[{step}] 시작 | {time}")`
- 무거운 작업은 `BackgroundTasks` 또는 `asyncio.to_thread()` 사용
- **MediaPipe 3D 사용 금지.** 위반 시 즉시 수정
- output/ 폴더 수동 수정 금지
