"""
test_rally_result.py — 랠리 result 판별 RED 테스트

현재 _split_rallies에서 result_val = "neutral" 하드코딩
→ assign_rally_result(positions, rally, court_data) 함수로 분리 구현 필요
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

COURT_DATA = {
    "corners": [[288, 108], [1632, 108], [1632, 1026], [288, 1026]],
    "homography": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    "frame_size": [1920, 1080],
}


class TestAssignRallyResultImport:
    def test_importable(self):
        """assign_rally_result 함수가 pipeline.rally에 존재해야 함"""
        from pipeline.rally import assign_rally_result  # noqa


class TestResultEnum:
    def test_result_is_valid_enum(self):
        """반환값은 반드시 'us' | 'them' | 'neutral' 중 하나"""
        from pipeline.rally import assign_rally_result
        rally = {"id": 1, "timestamp": {"start_sec": 0.0, "end_sec": 5.0}}
        positions = [(i, float(i * 10), 540.0, 1.0) for i in range(150)]
        result = assign_rally_result(positions, rally, COURT_DATA)
        assert result in ("us", "them", "neutral")

    def test_empty_positions_returns_neutral(self):
        """위치 데이터 없으면 neutral"""
        from pipeline.rally import assign_rally_result
        rally = {"id": 1, "timestamp": {"start_sec": 0.0, "end_sec": 5.0}}
        result = assign_rally_result([], rally, COURT_DATA)
        assert result == "neutral"


class TestResultDirection:
    def test_ball_exits_top_of_court_returns_them(self):
        """셔틀콕이 상단(y=0 방향) 밖으로 나가면 'them' (상대 진영 아웃)"""
        from pipeline.rally import assign_rally_result
        # y가 점점 줄어들어 0 이하로 나감 → 상단 아웃 → them
        positions = []
        for i in range(30):
            y = 540.0 - i * 20.0  # 마지막 프레임 y = 540 - 580 = -40 (화면 밖)
            conf = 1.0 if y > 0 else 0.0
            positions.append((i, 960.0, max(y, 0.0), conf))
        rally = {"id": 1, "timestamp": {"start_sec": 0.0, "end_sec": 1.0}}
        result = assign_rally_result(positions, rally, COURT_DATA)
        assert result == "them"

    def test_ball_exits_bottom_of_court_returns_us(self):
        """셔틀콕이 하단(y=max 방향) 밖으로 나가면 'us' (우리 진영 아웃)"""
        from pipeline.rally import assign_rally_result
        positions = []
        for i in range(30):
            y = 540.0 + i * 20.0  # 마지막 프레임 y → 1080 초과
            conf = 1.0 if y < 1080.0 else 0.0
            positions.append((i, 960.0, min(y, 1079.0), conf))
        rally = {"id": 1, "timestamp": {"start_sec": 0.0, "end_sec": 1.0}}
        result = assign_rally_result(positions, rally, COURT_DATA)
        assert result == "us"

    def test_ball_stays_in_court_returns_neutral(self):
        """셔틀콕이 코트 안에서만 움직이면 neutral"""
        from pipeline.rally import assign_rally_result
        positions = [(i, 960.0, 540.0, 1.0) for i in range(30)]
        rally = {"id": 1, "timestamp": {"start_sec": 0.0, "end_sec": 1.0}}
        result = assign_rally_result(positions, rally, COURT_DATA)
        assert result == "neutral"


class TestSplitRalliesUsesAssignment:
    def test_split_rallies_result_not_always_neutral(self):
        """
        _split_rallies 결과에서 result가 항상 'neutral'이면 안 됨.
        하드코딩 제거 후 assign_rally_result 호출해야 함.
        (현재 하드코딩이므로 이 테스트는 RED)
        """
        from pipeline.rally import _split_rallies
        import cv2

        # 셔틀콕이 상단으로 빠져나가는 positions 시뮬레이션
        positions = []
        # 랠리 시작: 속도 충분
        for i in range(10):
            positions.append((i, 960.0, 540.0 - i * 5, 1.0))
        # 미감지 31프레임 → 랠리 종료
        for i in range(10, 42):
            positions.append((i, 0.0, 0.0, 0.0))

        court = COURT_DATA
        # _split_rallies는 video_path를 쓰므로 dummy
        import unittest.mock as mock
        with mock.patch("cv2.VideoCapture") as mock_cap:
            instance = mock_cap.return_value
            instance.get.side_effect = lambda prop: {
                cv2.CAP_PROP_FPS: 30.0,
                cv2.CAP_PROP_FRAME_COUNT: 100,
            }.get(prop, 0)
            instance.release.return_value = None

            rallies = _split_rallies(positions, court, "dummy.mp4")

        if rallies:
            results = {r["result"] for r in rallies}
            # 적어도 하나는 neutral이 아니어야 함 (방향 감지 시)
            # 현재는 항상 neutral → RED
            assert "neutral" not in results or len(results) > 1, \
                "result가 전부 neutral — assign_rally_result 미연동 상태"
