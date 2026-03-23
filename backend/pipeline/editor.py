"""
editor.py — FFmpeg 기반 랠리 클립 & 숏폼 편집

입력: video_path, rallies list, job_id
출력: rallies에 clip_url, short_url 필드 추가된 리스트

TOP3 선정 공식:
    score = strokes * 2 + (10 if result == "us" else 0)
"""

import logging
import os
import subprocess

logger = logging.getLogger("ishuttle.pipeline.editor")


def score_rally(r: dict) -> int:
    return r["strokes"] * 2 + (10 if r.get("result") == "us" else 0)


def create_clips(video_path: str, rallies: list[dict], job_id: str) -> list[dict]:
    """
    각 랠리를 MP4 클립으로 잘라내고 TOP3는 9:16 숏폼도 생성한다.

    Fallback: FFmpeg 실패 시 clip_url = "" 로 설정
    """
    logger.info(f"[editor] 시작 | {len(rallies)}개 랠리")

    clips_dir = f"output/clips/{job_id}"
    shorts_dir = f"output/shorts/{job_id}"
    os.makedirs(clips_dir, exist_ok=True)
    os.makedirs(shorts_dir, exist_ok=True)

    top3 = sorted(rallies, key=score_rally, reverse=True)[:3]
    top3_ids = {r["id"] for r in top3}

    result_rallies = []
    for rally in rallies:
        rally = dict(rally)  # 복사
        try:
            clip_url = _cut_clip(video_path, rally, clips_dir, job_id)
            rally["clip_url"] = clip_url
        except Exception as e:
            logger.warning(f"[editor] 랠리 {rally['id']} 클립 실패: {e}")
            rally["clip_url"] = ""

        if rally["id"] in top3_ids:
            try:
                short_url = _create_short(video_path, rally, shorts_dir, job_id)
                rally["short_url"] = short_url
            except Exception as e:
                logger.warning(f"[editor] 랠리 {rally['id']} 숏폼 실패: {e}")
                rally["short_url"] = ""
        else:
            rally["short_url"] = ""

        result_rallies.append(rally)

    logger.info(f"[editor] 완료 | TOP3={[r['id'] for r in top3]}")
    return result_rallies


def _cut_clip(video_path: str, rally: dict, clips_dir: str, job_id: str) -> str:
    """FFmpeg으로 랠리 구간을 MP4 클립으로 추출"""
    rally_id = rally["id"]
    start = rally["timestamp"]["start_sec"]
    end = rally["timestamp"]["end_sec"]
    duration = max(end - start, 0.1)

    output_file = os.path.join(clips_dir, f"rally_{rally_id:03d}.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", video_path,
        "-t", str(duration),
        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
        "-c:a", "aac",
        "-movflags", "+faststart",
        output_file,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg clip 오류: {result.stderr[-200:]}")

    return f"/static/clips/{job_id}/rally_{rally_id:03d}.mp4"


def _create_short(video_path: str, rally: dict, shorts_dir: str, job_id: str) -> str:
    """
    9:16 숏폼 생성:
    - 중앙 크롭 (세로 풀 + 가로 중앙 9/16 비율)
    - 슬로우모션 (0.5배속)
    - 점수 오버레이
    """
    rally_id = rally["id"]
    start = rally["timestamp"]["start_sec"]
    end = rally["timestamp"]["end_sec"]
    duration = max(end - start, 0.1)
    score = rally.get("score_at_end", {})
    score_text = f"US {score.get('us', 0)} - {score.get('them', 0)} THEM"

    output_file = os.path.join(shorts_dir, f"rally_{rally_id:03d}_916.mp4")

    # 9:16 크롭 + 슬로우모션 + 텍스트 오버레이
    vf = (
        "scale=iw:-1,"
        "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,"
        "setpts=2.0*PTS,"  # 0.5배속 슬로우모션
        f"drawtext=text='{score_text}':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=50:box=1:boxcolor=black@0.5"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", video_path,
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
        "-c:a", "aac", "-af", "atempo=0.5",  # 오디오도 0.5배속
        "-movflags", "+faststart",
        output_file,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg short 오류: {result.stderr[-200:]}")

    return f"/static/shorts/{job_id}/rally_{rally_id:03d}_916.mp4"
