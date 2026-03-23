"""
heatmap.py — 선수 포지션 히트맵 PNG 생성

코트를 3×3 = 9구역으로 분할.
zone 번호: row * 3 + col
  0(좌상) 1(중상) 2(우상)
  3(좌중) 4(중중) 5(우중)
  6(좌하) 7(중하) 8(우하)

입력: player_tracks (dict), court_data (dict), output_path (str)
출력: output_path (str) — PNG 파일 저장 후 경로 반환
"""

import logging
import os

import numpy as np
from PIL import Image, ImageDraw

logger = logging.getLogger("ishuttle.pipeline.heatmap")

ZONES = 9
GRID_ROWS = 3
GRID_COLS = 3
IMG_W = 612   # 코트 폭 비율 (6.1m)
IMG_H = 1340  # 코트 길이 비율 (13.4m)


def get_zone_counts(player_tracks: dict) -> dict[int, int]:
    """
    선수 트랙 데이터에서 각 zone에 머문 총 프레임 수를 반환.
    x, y는 0~1 정규화 좌표.
    """
    counts: dict[int, int] = {i: 0 for i in range(ZONES)}

    players = player_tracks.get("players", {})
    for pid, frames in players.items():
        for frame_data in frames:
            x = frame_data.get("x", 0.0)
            y = frame_data.get("y", 0.0)
            zone = _xy_to_zone(x, y)
            counts[zone] += 1

    return counts


def _xy_to_zone(x: float, y: float) -> int:
    """정규화 좌표 (0~1) → zone 번호 (0~8)"""
    col = min(int(x * GRID_COLS), GRID_COLS - 1)
    row = min(int(y * GRID_ROWS), GRID_ROWS - 1)
    return row * GRID_COLS + col


def generate_heatmap(player_tracks: dict, court_data: dict, output_path: str) -> str:
    """
    선수 포지션 히트맵 PNG를 생성하고 output_path에 저장한다.

    Returns:
        output_path (저장된 파일 경로)
    """
    logger.info(f"[heatmap] 생성 시작 → {output_path}")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    counts = get_zone_counts(player_tracks)
    max_count = max(counts.values()) if counts else 1
    if max_count == 0:
        max_count = 1

    # 코트 배경 이미지 (흰색)
    img = Image.new("RGB", (IMG_W, IMG_H), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)

    cell_w = IMG_W // GRID_COLS
    cell_h = IMG_H // GRID_ROWS

    for zone, count in counts.items():
        row = zone // GRID_COLS
        col = zone % GRID_COLS

        x0 = col * cell_w
        y0 = row * cell_h
        x1 = x0 + cell_w
        y1 = y0 + cell_h

        intensity = count / max_count  # 0.0 ~ 1.0
        color = _intensity_to_color(intensity)
        draw.rectangle([x0, y0, x1, y1], fill=color)

    # 코트 라인 그리기
    _draw_court_lines(draw, cell_w, cell_h)

    img.save(output_path, format="PNG")
    logger.info(f"[heatmap] 저장 완료 | size={os.path.getsize(output_path)}bytes")

    return output_path


def _intensity_to_color(intensity: float) -> tuple[int, int, int]:
    """
    intensity (0~1) → RGB 색상
    낮음: 파란색(#3498db) → 높음: 빨간색(#e74c3c)
    """
    r = int(52 + (231 - 52) * intensity)   # 52 → 231
    g = int(152 + (76 - 152) * intensity)  # 152 → 76
    b = int(219 + (60 - 219) * intensity)  # 219 → 60
    return (r, g, b)


def _draw_court_lines(draw: ImageDraw.Draw, cell_w: int, cell_h: int) -> None:
    """3×3 그리드 라인 및 코트 외곽 라인 그리기"""
    line_color = (80, 80, 80)
    line_width = 2

    # 수직 그리드 라인
    for col in range(1, GRID_COLS):
        x = col * cell_w
        draw.line([(x, 0), (x, IMG_H)], fill=line_color, width=line_width)

    # 수평 그리드 라인
    for row in range(1, GRID_ROWS):
        y = row * cell_h
        draw.line([(0, y), (IMG_W, y)], fill=line_color, width=line_width)

    # 외곽 테두리
    draw.rectangle([0, 0, IMG_W - 1, IMG_H - 1], outline=line_color, width=line_width)
