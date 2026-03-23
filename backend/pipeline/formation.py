"""
formation.py — 포메이션 분류기

입력: rallies (list[dict]), player_tracks (dict)
출력: rallies에 formation 필드 추가된 리스트

분류 기준 (촬영 측 두 선수의 코트 좌표):
- front_back: dy > dx * 1.5  → 전후 공격 포메이션
- side_by_side: dx > dy * 1.5 → 좌우 수비 포메이션
- transition: 그 외           → 과도기
"""

import logging

logger = logging.getLogger("ishuttle.pipeline.formation")


def classify_formation(p1_y: float, p1_x: float, p2_y: float, p2_x: float) -> str:
    """두 선수 좌표 → 포메이션 분류"""
    dy = abs(p1_y - p2_y)
    dx = abs(p1_x - p2_x)

    if dy > dx * 1.5:
        return "front_back"
    elif dx > dy * 1.5:
        return "side_by_side"
    else:
        return "transition"


def classify_all_formations(rallies: list[dict], player_tracks: dict) -> list[dict]:
    """
    각 랠리 구간의 포메이션을 분류하여 rallies에 추가한다.
    """
    logger.info(f"[formation] {len(rallies)}개 랠리 포메이션 분류 시작")

    fps = player_tracks.get("fps", 30.0)
    players = player_tracks.get("players", {})

    # 촬영 측 선수 ID (1, 2 = 촬영 측 / 3, 4 = 상대측 가정)
    # 실제로는 게임 설정의 팀 색상·위치 앵커 기반으로 결정
    our_player_ids = ["1", "2"]

    result_rallies = []
    for rally in rallies:
        rally = dict(rally)
        start_sec = rally["timestamp"]["start_sec"]
        end_sec = rally["timestamp"]["end_sec"]

        formation = _classify_rally_formation(
            start_sec, end_sec, fps, players, our_player_ids
        )
        rally["formation"] = formation
        result_rallies.append(rally)

    logger.info("[formation] 완료")
    return result_rallies


def _classify_rally_formation(
    start_sec: float,
    end_sec: float,
    fps: float,
    players: dict,
    our_player_ids: list[str],
) -> dict:
    """랠리 구간의 dominant 포메이션과 transition 횟수를 반환"""
    start_frame = int(start_sec * fps)
    end_frame = int(end_sec * fps)

    if not all(pid in players for pid in our_player_ids):
        return {"dominant": "transition", "transitions": 0}

    p1_tracks = players[our_player_ids[0]]
    p2_tracks = players[our_player_ids[1]]

    # 랠리 구간 프레임 필터
    p1_in_rally = [f for f in p1_tracks if start_frame <= f["frame"] <= end_frame]
    p2_in_rally = [f for f in p2_tracks if start_frame <= f["frame"] <= end_frame]

    if not p1_in_rally or not p2_in_rally:
        return {"dominant": "transition", "transitions": 0}

    # 공통 프레임으로 포메이션 시퀀스 생성
    p1_by_frame = {f["frame"]: f for f in p1_in_rally}
    p2_by_frame = {f["frame"]: f for f in p2_in_rally}
    common_frames = sorted(set(p1_by_frame.keys()) & set(p2_by_frame.keys()))

    if not common_frames:
        return {"dominant": "transition", "transitions": 0}

    formation_seq = []
    for frame in common_frames:
        f1 = classify_formation(
            p1_by_frame[frame]["y"], p1_by_frame[frame]["x"],
            p2_by_frame[frame]["y"], p2_by_frame[frame]["x"],
        )
        formation_seq.append(f1)

    # dominant 포메이션: 가장 많이 나온 값
    from collections import Counter
    counts = Counter(formation_seq)
    dominant = counts.most_common(1)[0][0]

    # transition 횟수: 포메이션이 바뀐 횟수
    transitions = sum(1 for i in range(1, len(formation_seq)) if formation_seq[i] != formation_seq[i - 1])

    return {"dominant": dominant, "transitions": transitions}
