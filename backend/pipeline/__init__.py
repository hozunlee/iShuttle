"""
iShuttle AI 파이프라인 — 6단계 순차 실행

OOM 방지: 각 단계 종료 후 모델 즉시 해제
순서: court → tracker → rally → editor → formation+pose → reporter
"""

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial

_executor = ThreadPoolExecutor(max_workers=1)


async def _run_sync(fn, *args):
    """동기 CPU 블로킹 함수를 스레드 풀에서 실행 — 이벤트 루프 차단 방지"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, partial(fn, *args))

logger = logging.getLogger("ishuttle.pipeline")

STEPS = [
    (10,  "코트 라인 감지 중..."),
    (30,  "선수 추적 중..."),
    (55,  "랠리 분리 중..."),
    (70,  "클립 편집 중..."),
    (85,  "포메이션·자세 분석 중..."),
    (95,  "AI 리포트 생성 중..."),
    (100, "완료"),
]


async def _push_progress(job_id: str, progress: int, step: str, jobs: dict, ws_subscribers: dict):
    """job 상태 업데이트 + WebSocket 구독자에게 push"""
    jobs[job_id]["progress"] = progress
    jobs[job_id]["step"] = step

    subscribers = ws_subscribers.get(job_id, [])
    if subscribers:
        payload = {"progress": progress, "step": step, "status": jobs[job_id]["status"]}
        dead = []
        for ws in subscribers:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            subscribers.remove(ws)


async def run_pipeline(
    job_id: str,
    video_path: str,
    game_config: dict,
    jobs: dict,
    ws_subscribers: dict,
):
    """
    AI 파이프라인 6단계를 순차 실행한다.
    각 단계 완료 후 진행률을 WebSocket으로 push한다.
    """
    logger.info(f"[pipeline] job_id={job_id} 시작 | video={video_path}")
    start_time = datetime.now()

    try:
        # ① 코트 감지
        await _push_progress(job_id, 5, "코트 라인 감지 중...", jobs, ws_subscribers)
        from pipeline.court import detect_court
        court_data = await _run_sync(detect_court, video_path)
        logger.info(f"[pipeline] ① court 완료")
        await _push_progress(job_id, 10, "코트 감지 완료", jobs, ws_subscribers)

        # ② 선수 추적
        await _push_progress(job_id, 15, "선수 추적 중...", jobs, ws_subscribers)
        from pipeline.tracker import track_players
        player_tracks = await _run_sync(track_players, video_path, court_data)
        logger.info(f"[pipeline] ② tracker 완료")
        await _push_progress(job_id, 30, "선수 추적 완료", jobs, ws_subscribers)

        # ③ 셔틀콕 추적 & 랠리 분리
        await _push_progress(job_id, 35, "셔틀콕 추적 & 랠리 분리 중...", jobs, ws_subscribers)
        from pipeline.rally import detect_rallies
        our_side = game_config.get("our_side", "bottom")
        rallies = await _run_sync(detect_rallies, video_path, court_data, our_side)
        logger.info(f"[pipeline] ③ rally 완료: {len(rallies)}개 랠리")
        await _push_progress(job_id, 55, f"랠리 {len(rallies)}개 감지 완료", jobs, ws_subscribers)

        # ④ 클립 편집 (랠리별 MP4 + 숏폼)
        await _push_progress(job_id, 60, "랠리 클립 편집 중...", jobs, ws_subscribers)
        from pipeline.editor import create_clips
        rallies_with_clips = await _run_sync(create_clips, video_path, rallies, job_id)
        logger.info(f"[pipeline] ④ editor 완료")
        await _push_progress(job_id, 70, "클립 편집 완료", jobs, ws_subscribers)

        # ⑤-A 포메이션 분류
        await _push_progress(job_id, 75, "포메이션 분류 중...", jobs, ws_subscribers)
        from pipeline.formation import classify_all_formations
        rallies_with_formation = await _run_sync(classify_all_formations, rallies_with_clips, player_tracks)
        logger.info(f"[pipeline] ⑤-A formation 완료")

        # ⑤-B 자세 분석
        await _push_progress(job_id, 80, "자세 분석 중...", jobs, ws_subscribers)
        from pipeline.pose import analyze_pose
        pose_summary = await _run_sync(analyze_pose, video_path, rallies_with_formation)
        logger.info(f"[pipeline] ⑤-B pose 완료")
        await _push_progress(job_id, 85, "자세 분석 완료", jobs, ws_subscribers)

        # ⑤-C 히트맵 생성
        await _push_progress(job_id, 87, "히트맵 생성 중...", jobs, ws_subscribers)
        from pipeline.heatmap import generate_heatmap
        import uuid as _uuid
        _heatmap_game_id = str(_uuid.uuid4())
        heatmap_dir = f"output/heatmap"
        os.makedirs(heatmap_dir, exist_ok=True)
        heatmap_path = f"{heatmap_dir}/{_heatmap_game_id}.png"
        await _run_sync(generate_heatmap, player_tracks, court_data, heatmap_path)
        logger.info(f"[pipeline] ⑤-C heatmap 완료")

        # ⑥ AI 리포트 생성
        await _push_progress(job_id, 90, "AI 리포트 생성 중...", jobs, ws_subscribers)
        from pipeline.reporter import generate_report
        import uuid
        game_id = str(uuid.uuid4())
        game_data = {
            "game_id": game_id,
            "game_config": game_config,
            "rallies": rallies_with_formation,
            "pose_summary": pose_summary,
        }
        ai_report = await _run_sync(generate_report, game_data)
        logger.info(f"[pipeline] ⑥ reporter 완료")

        # 최종 RallyReport 조립
        result = _build_rally_report(game_id, game_config, rallies_with_formation, pose_summary, ai_report, _heatmap_game_id)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"[pipeline] job_id={job_id} 완료 | 소요: {elapsed:.1f}s")

        jobs[job_id]["status"] = "done"
        jobs[job_id]["result"] = result
        await _push_progress(job_id, 100, "분석 완료!", jobs, ws_subscribers)

    except Exception as e:
        logger.error(f"[pipeline] job_id={job_id} 오류: {e}", exc_info=True)
        jobs[job_id]["status"] = "error"
        jobs[job_id]["step"] = f"오류: {str(e)}"
        await _push_progress(job_id, jobs[job_id]["progress"], f"오류 발생: {str(e)}", jobs, ws_subscribers)


def _build_rally_report(game_id, game_config, rallies, pose_summary, ai_report, heatmap_game_id=None) -> dict:
    """파이프라인 결과물을 RallyReport JSON 스키마로 조립"""
    mode = game_config.get("rule_mode", "amateur")

    rule = {
        "mode": mode,
        "win_score": 25,
        "deuce_trigger": 24,
        "deuce_cap": 31,
        "court_change_at": 13,
    }

    # 최종 스코어 계산
    us_score = sum(1 for r in rallies if r.get("result") == "us")
    them_score = sum(1 for r in rallies if r.get("result") == "them")

    return {
        "game_id": game_id,
        "rule": rule,
        "score": {"us": us_score, "them": them_score},
        "rallies": rallies,
        "heatmap_url": f"/static/heatmap/{heatmap_game_id or game_id}.png",
        "pose_summary": pose_summary,
        "ai_report": ai_report,
    }
