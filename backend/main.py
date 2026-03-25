"""iShuttle FastAPI 앱 진입점"""

import asyncio
import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.analyze import router as analyze_router
from api.results import router as results_router
from api.feedback import router as feedback_router
from api.report import router as report_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("ishuttle")

# 인메모리 job 상태 저장소
# { job_id: { "progress": 0~100, "step": str, "status": "processing"|"done"|"error", "result": dict|None } }
jobs: dict[str, dict] = {}

# WebSocket 구독자 목록
# { job_id: [WebSocket, ...] }
ws_subscribers: dict[str, list[WebSocket]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    import os
    os.makedirs("output/clips", exist_ok=True)
    os.makedirs("output/shorts", exist_ok=True)
    os.makedirs("output/heatmap", exist_ok=True)
    logger.info("iShuttle 백엔드 시작. output/ 디렉토리 준비 완료.")
    yield
    logger.info("iShuttle 백엔드 종료.")


app = FastAPI(title="iShuttle API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (AI 파이프라인 결과물)
import os
if os.path.exists("output"):
    app.mount("/static", StaticFiles(directory="output"), name="static")

# 라우터 등록
app.include_router(analyze_router, prefix="/api")
app.include_router(results_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")
app.include_router(report_router, prefix="/api")

# jobs / ws_subscribers를 라우터에 공유
app.state.jobs = jobs
app.state.ws_subscribers = ws_subscribers


@app.get("/health")
async def health():
    return {"status": "ok", "jobs": len(jobs)}


@app.websocket("/ws/progress/{job_id}")
async def ws_progress(websocket: WebSocket, job_id: str):
    await websocket.accept()

    if job_id not in ws_subscribers:
        ws_subscribers[job_id] = []
    ws_subscribers[job_id].append(websocket)

    logger.info(f"[WS] {job_id} 구독 시작")

    try:
        # 현재 상태 즉시 전송
        if job_id in jobs:
            job = jobs[job_id]
            await websocket.send_json({
                "progress": job["progress"],
                "step": job["step"],
                "status": job["status"],
            })

        # 연결 유지 (ping/pong)
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"ping": True})
    except (WebSocketDisconnect, RuntimeError):
        logger.info(f"[WS] {job_id} 구독 종료")
    finally:
        if job_id in ws_subscribers:
            ws_subscribers[job_id] = [w for w in ws_subscribers[job_id] if w != websocket]
