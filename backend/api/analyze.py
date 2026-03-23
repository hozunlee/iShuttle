"""POST /api/analyze — 영상 업로드 & 분석 시작"""

import json
import logging
import os
import shutil
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Request, UploadFile, File, Form, HTTPException

from pipeline import run_pipeline

logger = logging.getLogger("ishuttle.api.analyze")
router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/analyze")
async def analyze(
    request: Request,
    background_tasks: BackgroundTasks,
    video_file: UploadFile = File(...),
    game_config: str = Form(...),
):
    """
    영상 파일을 업로드하고 AI 파이프라인 분석을 시작한다.

    Returns:
        { job_id: str, status: "processing" }
    """
    try:
        game_config_dict = json.loads(game_config)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="game_config JSON 파싱 실패")

    job_id = str(uuid4())

    # 영상 파일 저장
    video_path = os.path.join(UPLOAD_DIR, f"{job_id}_{video_file.filename}")
    with open(video_path, "wb") as f:
        shutil.copyfileobj(video_file.file, f)

    # 초기 job 상태 등록
    jobs = request.app.state.jobs
    jobs[job_id] = {
        "progress": 0,
        "step": "대기 중...",
        "status": "processing",
        "result": None,
    }

    logger.info(f"[analyze] job_id={job_id} 생성. 파일: {video_path}")

    # 백그라운드 파이프라인 실행
    background_tasks.add_task(
        run_pipeline,
        job_id=job_id,
        video_path=video_path,
        game_config=game_config_dict,
        jobs=jobs,
        ws_subscribers=request.app.state.ws_subscribers,
    )

    return {"job_id": job_id, "status": "processing"}


@router.get("/status/{job_id}")
async def get_status(job_id: str, request: Request):
    """
    분석 진행 상태를 반환한다.

    Returns:
        { progress: int, step: str }
    """
    jobs = request.app.state.jobs
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="job_id를 찾을 수 없습니다")

    job = jobs[job_id]
    return {"progress": job["progress"], "step": job["step"], "status": job["status"]}
