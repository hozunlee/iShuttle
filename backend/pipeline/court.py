"""
court.py — 코트 4꼭짓점 감지 & 호모그래피 행렬 계산

입력: video_path (str)
출력: {
    "corners": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],  # 코트 4꼭짓점 (픽셀 좌표)
    "homography": [[...], [...], [...]],                  # 3x3 호모그래피 행렬
    "frame_size": [width, height]
}
"""

import logging
import traceback
from typing import Optional

logger = logging.getLogger("ishuttle.pipeline.court")

# 실제 배드민턴 코트 크기 (mm)
COURT_WIDTH_MM = 6100   # 복식 코트 폭
COURT_HEIGHT_MM = 13400  # 코트 길이


def detect_court(video_path: str) -> dict:
    """
    영상에서 배드민턴 코트 4꼭짓점을 감지하고 호모그래피를 계산한다.

    Fallback: 감지 실패 시 영상 크기 기반 추정값 반환
    """
    logger.info(f"[court] 시작 | {video_path}")

    try:
        result = _detect_with_opencv(video_path)
        logger.info(f"[court] OpenCV 감지 성공: corners={result['corners']}")
        return result
    except Exception as e:
        logger.warning(f"[court] OpenCV 감지 실패, fallback 사용: {e}")
        return _fallback_court(video_path)


def _detect_with_opencv(video_path: str) -> dict:
    """OpenCV Hough 라인 기반 코트 감지"""
    import cv2
    import numpy as np

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"영상 열기 실패: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # 중간 프레임에서 코트 감지 시도
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError("프레임 읽기 실패")

    # 그레이스케일 → 엣지 검출
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150, apertureSize=3)

    # Hough 라인 변환
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=20)

    if lines is None or len(lines) < 4:
        raise RuntimeError("코트 라인 감지 실패 (라인 수 부족)")

    # TODO: 실제 코트 4꼭짓점 추출 알고리즘 구현
    # 현재는 간단한 추정값 사용
    corners = _estimate_corners_from_lines(lines, width, height)
    homography = _compute_homography(corners, width, height)

    return {
        "corners": corners,
        "homography": homography.tolist(),
        "frame_size": [width, height],
    }


def _estimate_corners_from_lines(lines, width: int, height: int) -> list:
    """라인에서 코트 4꼭짓점 추정 (간소화 버전)"""
    # 실제 구현에서는 교점 계산 필요
    # 현재는 화면 비율 기반 추정
    margin_x = int(width * 0.15)
    margin_top = int(height * 0.1)
    margin_bottom = int(height * 0.05)

    return [
        [margin_x, margin_top],                    # 좌상단
        [width - margin_x, margin_top],            # 우상단
        [width - margin_x, height - margin_bottom],# 우하단
        [margin_x, height - margin_bottom],        # 좌하단
    ]


def _compute_homography(corners: list, width: int, height: int):
    """4꼭짓점 → 탑뷰 호모그래피 행렬 계산"""
    import numpy as np
    import cv2

    src = np.float32(corners)
    dst = np.float32([
        [0, 0],
        [COURT_WIDTH_MM, 0],
        [COURT_WIDTH_MM, COURT_HEIGHT_MM],
        [0, COURT_HEIGHT_MM],
    ])

    H, _ = cv2.findHomography(src, dst)
    return H if H is not None else np.eye(3)


def _fallback_court(video_path: str) -> dict:
    """감지 실패 시 영상 크기 기반 추정 코트 반환"""
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
        cap.release()
    except Exception:
        width, height = 1920, 1080

    margin_x = int(width * 0.15)
    margin_top = int(height * 0.10)
    margin_bottom = int(height * 0.05)

    corners = [
        [margin_x, margin_top],
        [width - margin_x, margin_top],
        [width - margin_x, height - margin_bottom],
        [margin_x, height - margin_bottom],
    ]

    import numpy as np
    homography = np.eye(3).tolist()

    logger.warning("[court] fallback 코트 좌표 사용")
    return {
        "corners": corners,
        "homography": homography,
        "frame_size": [width, height],
        "is_fallback": True,
    }
