"""GET /api/results/{job_id} — 분석 결과 반환"""

import logging
from fastapi import APIRouter, Request, HTTPException

logger = logging.getLogger("ishuttle.api.results")
router = APIRouter()


@router.get("/results/{job_id}")
async def get_results(job_id: str, request: Request):
    """
    완료된 분석 결과 RallyReport JSON을 반환한다.

    Returns:
        RallyReport JSON
    """
    jobs = request.app.state.jobs
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="job_id를 찾을 수 없습니다")

    job = jobs[job_id]

    if job["status"] == "processing":
        raise HTTPException(status_code=202, detail="아직 분석 중입니다")

    if job["status"] == "error":
        raise HTTPException(status_code=500, detail="파이프라인 오류가 발생했습니다")

    if job["result"] is None:
        raise HTTPException(status_code=500, detail="결과 데이터가 없습니다")

    return job["result"]
