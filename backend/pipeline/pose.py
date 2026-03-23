"""
pose.py — MediaPipe Pose 2D 자세 분석

규칙:
- model_complexity=1 고정
- 3D 키포인트 사용 금지
- visibility < 0.5 프레임은 해당 관절 confidence=low 처리
- 후면 촬영 기준: 어깨(11,12), 골반(23,24), 무릎(25,26), 발목(27,28) 관절 사용

입력: video_path, rallies
출력: {
    "shoulder_rotation_avg": float,  # 어깨 회전각 (도)
    "spine_tilt_avg": float,          # 척추 기울기 (도)
    "knee_bend_avg": float,           # 무릎 굽힘각 (도)
    "confidence": "high" | "medium" | "low"
}
"""

import logging
import math
from typing import Optional

logger = logging.getLogger("ishuttle.pipeline.pose")

# MediaPipe 랜드마크 인덱스
LM_LEFT_SHOULDER = 11
LM_RIGHT_SHOULDER = 12
LM_LEFT_HIP = 23
LM_RIGHT_HIP = 24
LM_LEFT_KNEE = 25
LM_RIGHT_KNEE = 26
LM_LEFT_ANKLE = 27
LM_RIGHT_ANKLE = 28

VISIBILITY_THRESHOLD = 0.5


def analyze_pose(video_path: str, rallies: list[dict]) -> dict:
    """
    랠리별 스윙 순간의 자세를 분석하고 평균 수치를 반환한다.

    Fallback: MediaPipe 실패 시 confidence=low mock 데이터 반환
    """
    logger.info(f"[pose] 시작 | {video_path}")

    try:
        result = _analyze_with_mediapipe(video_path, rallies)
        logger.info(f"[pose] MediaPipe 완료: {result}")
        return result
    except Exception as e:
        logger.warning(f"[pose] MediaPipe 실패, fallback 사용: {e}")
        return _fallback_pose()


def _analyze_with_mediapipe(video_path: str, rallies: list[dict]) -> dict:
    """MediaPipe Pose로 자세 분석"""
    import mediapipe as mp
    import cv2

    mp_pose = mp.solutions.pose
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    shoulder_rotations = []
    spine_tilts = []
    knee_bends = []
    confidence_scores = []

    with mp_pose.Pose(model_complexity=1, static_image_mode=False) as pose:
        for rally in rallies:
            # 랠리 중간 프레임 분석 (스윙 순간 근사)
            mid_sec = (rally["timestamp"]["start_sec"] + rally["timestamp"]["end_sec"]) / 2
            target_frame = int(mid_sec * fps)

            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            if not ret:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            if not results.pose_landmarks:
                continue

            lm = results.pose_landmarks.landmark

            # visibility 체크
            key_landmarks = [LM_LEFT_SHOULDER, LM_RIGHT_SHOULDER, LM_LEFT_HIP, LM_RIGHT_HIP, LM_LEFT_KNEE, LM_RIGHT_KNEE]
            visibilities = [lm[i].visibility for i in key_landmarks]
            min_vis = min(visibilities)
            confidence_scores.append(min_vis)

            if min_vis < VISIBILITY_THRESHOLD:
                continue

            # 어깨 회전각 계산
            shoulder_angle = _calc_angle_2d(
                (lm[LM_LEFT_SHOULDER].x, lm[LM_LEFT_SHOULDER].y),
                (lm[LM_RIGHT_SHOULDER].x, lm[LM_RIGHT_SHOULDER].y),
            )
            shoulder_rotations.append(shoulder_angle)

            # 척추 기울기: 어깨 중점 → 골반 중점 각도
            shoulder_mid = (
                (lm[LM_LEFT_SHOULDER].x + lm[LM_RIGHT_SHOULDER].x) / 2,
                (lm[LM_LEFT_SHOULDER].y + lm[LM_RIGHT_SHOULDER].y) / 2,
            )
            hip_mid = (
                (lm[LM_LEFT_HIP].x + lm[LM_RIGHT_HIP].x) / 2,
                (lm[LM_LEFT_HIP].y + lm[LM_RIGHT_HIP].y) / 2,
            )
            spine_angle = _calc_spine_tilt(shoulder_mid, hip_mid)
            spine_tilts.append(spine_angle)

            # 무릎 굽힘각 (왼쪽 무릎)
            knee_angle = _calc_knee_bend(
                (lm[LM_LEFT_HIP].x, lm[LM_LEFT_HIP].y),
                (lm[LM_LEFT_KNEE].x, lm[LM_LEFT_KNEE].y),
                (lm[LM_LEFT_ANKLE].x, lm[LM_LEFT_ANKLE].y),
            )
            knee_bends.append(knee_angle)

    cap.release()

    # 모델 메모리 해제
    import gc
    gc.collect()

    if not shoulder_rotations:
        return _fallback_pose()

    avg_conf = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    if avg_conf >= 0.7:
        confidence = "high"
    elif avg_conf >= 0.5:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "shoulder_rotation_avg": round(sum(shoulder_rotations) / len(shoulder_rotations), 1),
        "spine_tilt_avg": round(sum(spine_tilts) / len(spine_tilts), 1) if spine_tilts else 0.0,
        "knee_bend_avg": round(sum(knee_bends) / len(knee_bends), 1) if knee_bends else 0.0,
        "confidence": confidence,
    }


def _calc_angle_2d(p1: tuple, p2: tuple) -> float:
    """두 점을 잇는 벡터의 수평선 기준 각도 (도)"""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle = math.degrees(math.atan2(abs(dy), abs(dx)))
    return round(angle, 2)


def _calc_spine_tilt(shoulder_mid: tuple, hip_mid: tuple) -> float:
    """어깨 중점 → 골반 중점 벡터의 수직선 기준 기울기 (도)"""
    dx = hip_mid[0] - shoulder_mid[0]
    dy = hip_mid[1] - shoulder_mid[1]
    angle = math.degrees(math.atan2(abs(dx), abs(dy)))
    return round(angle, 2)


def _calc_knee_bend(hip: tuple, knee: tuple, ankle: tuple) -> float:
    """세 점으로 무릎 굽힘각 계산 (도)"""
    v1 = (hip[0] - knee[0], hip[1] - knee[1])
    v2 = (ankle[0] - knee[0], ankle[1] - knee[1])

    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    mag2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)

    if mag1 == 0 or mag2 == 0:
        return 180.0

    cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return round(math.degrees(math.acos(cos_angle)), 2)


def _fallback_pose() -> dict:
    """MediaPipe 실패 시 confidence=low mock 데이터 반환"""
    logger.warning("[pose] fallback mock 자세 데이터 사용")
    return {
        "shoulder_rotation_avg": 0.0,
        "spine_tilt_avg": 0.0,
        "knee_bend_avg": 0.0,
        "confidence": "low",
    }
