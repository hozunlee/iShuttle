"""POST /api/feedback — 선택 랠리 기반 AI 피드백"""

import logging
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("ishuttle.api.feedback")
router = APIRouter()


class FeedbackRequest(BaseModel):
    game_id: str
    rally_ids: list[int]


@router.post("/feedback")
async def get_feedback(body: FeedbackRequest, request: Request):
    """
    선택한 랠리 ID 목록을 기반으로 AI 피드백을 생성한다.

    Returns:
        { summary, pros, cons, focus }
    """
    jobs = request.app.state.jobs

    # game_id로 결과 찾기
    target_job = None
    for job in jobs.values():
        if job.get("result") and job["result"].get("game_id") == body.game_id:
            target_job = job
            break

    if target_job is None:
        raise HTTPException(status_code=404, detail="게임 결과를 찾을 수 없습니다")

    result = target_job["result"]
    selected_rallies = [r for r in result.get("rallies", []) if r["id"] in body.rally_ids]

    if not selected_rallies:
        raise HTTPException(status_code=422, detail="선택된 랠리가 없습니다")

    # reporter를 통해 피드백 생성
    try:
        from pipeline.reporter import generate_feedback
        feedback = await generate_feedback(result, selected_rallies)
        return feedback
    except Exception as e:
        logger.error(f"[feedback] 오류: {e}")
        raise HTTPException(status_code=500, detail=f"피드백 생성 실패: {str(e)}")
