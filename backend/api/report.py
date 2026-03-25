"""POST /api/report — 랠리 신고 접수 & JSONL 저장"""

import json
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger("ishuttle.api.report")
router = APIRouter()

REPORT_FILE = "output/reports.jsonl"
VALID_REASONS = {"non_game", "boundary_error", "score_error", "other"}


class ReportRequest(BaseModel):
    rally_id: int
    job_id: str
    reason: str
    comment: str = ""


@router.post("/report")
async def submit_report(body: ReportRequest):
    """
    잘못 감지된 랠리를 신고한다.
    신고 데이터를 output/reports.jsonl 에 append한다.

    Returns:
        { ok: True }
    """
    reason = body.reason if body.reason in VALID_REASONS else "other"

    entry = {
        "rally_id": body.rally_id,
        "job_id": body.job_id,
        "reason": reason,
        "comment": body.comment.strip(),
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs("output", exist_ok=True)
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info(f"[report] 신고 접수: rally_id={body.rally_id} job_id={body.job_id} reason={reason}")
    return {"ok": True}
