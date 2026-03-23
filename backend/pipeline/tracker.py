"""
tracker.py — YOLOv8n-pose + ByteTrack 선수 4명 추적

입력: video_path, court_data
출력: {
    "players": {
        "1": [{"frame": int, "x": float, "y": float, "keypoints": [[x,y,conf], ...]}, ...],
        "2": [...], "3": [...], "4": [...]
    },
    "fps": float,
    "total_frames": int
}
"""

import logging

logger = logging.getLogger("ishuttle.pipeline.tracker")


def track_players(video_path: str, court_data: dict) -> dict:
    """
    YOLOv8n-pose + ByteTrack으로 선수 4명을 추적한다.

    Fallback: YOLO 실패 시 mock 데이터 반환
    """
    logger.info(f"[tracker] 시작 | {video_path}")

    try:
        result = _track_with_yolo(video_path, court_data)
        logger.info(f"[tracker] YOLO 추적 완료: 선수 {len(result['players'])}명")
        return result
    except Exception as e:
        logger.warning(f"[tracker] YOLO 추적 실패, fallback 사용: {e}")
        return _fallback_tracks(video_path)


def _track_with_yolo(video_path: str, court_data: dict) -> dict:
    """YOLOv8n-pose + ByteTrack으로 선수 추적"""
    from ultralytics import YOLO
    import cv2

    model = YOLO("yolov8n-pose.pt")

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    results = model.track(
        source=video_path,
        persist=True,
        tracker="bytetrack.yaml",
        conf=0.5,
        iou=0.5,
        verbose=False,
    )

    players: dict[str, list] = {}

    for frame_idx, result in enumerate(results):
        if result.boxes.id is None:
            continue

        ids = result.boxes.id.int().tolist()
        boxes = result.boxes.xywh.tolist()
        keypoints_data = result.keypoints.xy.tolist() if result.keypoints else []
        confs = result.keypoints.conf.tolist() if result.keypoints and result.keypoints.conf is not None else []

        for i, player_id in enumerate(ids):
            pid = str(player_id)
            if pid not in players:
                players[pid] = []

            x_center = boxes[i][0] / result.orig_shape[1]
            y_center = boxes[i][1] / result.orig_shape[0]

            kps = []
            if i < len(keypoints_data):
                for ki, kp in enumerate(keypoints_data[i]):
                    conf = confs[i][ki] if i < len(confs) and ki < len(confs[i]) else 0.0
                    kps.append([kp[0], kp[1], conf])

            players[pid].append({
                "frame": frame_idx,
                "x": x_center,
                "y": y_center,
                "keypoints": kps,
            })

    # 모델 메모리 해제
    del model
    import gc
    gc.collect()

    # 감지 횟수 상위 4명만 유지 (ByteTrack ID 파편화 제거)
    sorted_ids = sorted(players.keys(), key=lambda pid: len(players[pid]), reverse=True)
    top4 = sorted_ids[:4]
    players = {str(i + 1): players[pid] for i, pid in enumerate(top4)}
    logger.info(f"[tracker] 상위 4명 필터링: {sorted_ids[:4]} → player 1~4")

    return {
        "players": players,
        "fps": fps,
        "total_frames": total_frames,
    }


def _fallback_tracks(video_path: str) -> dict:
    """추적 실패 시 mock 선수 데이터 반환"""
    import cv2

    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1800
        cap.release()
    except Exception:
        fps, total_frames = 30.0, 1800

    logger.warning("[tracker] fallback mock 선수 데이터 사용")

    # 4명 선수 고정 위치 mock
    players = {
        "1": [{"frame": f, "x": 0.25, "y": 0.25, "keypoints": []} for f in range(0, total_frames, 3)],
        "2": [{"frame": f, "x": 0.75, "y": 0.25, "keypoints": []} for f in range(0, total_frames, 3)],
        "3": [{"frame": f, "x": 0.25, "y": 0.75, "keypoints": []} for f in range(0, total_frames, 3)],
        "4": [{"frame": f, "x": 0.75, "y": 0.75, "keypoints": []} for f in range(0, total_frames, 3)],
    }

    return {"players": players, "fps": fps, "total_frames": total_frames}
