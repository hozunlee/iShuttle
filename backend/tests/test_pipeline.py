"""iShuttle 파이프라인 유닛 테스트"""

import asyncio
import pytest


class TestFormation:
    def test_front_back(self):
        from pipeline.formation import classify_formation
        # dy > dx * 1.5 → front_back
        assert classify_formation(0.2, 0.5, 0.8, 0.5) == "front_back"

    def test_side_by_side(self):
        from pipeline.formation import classify_formation
        # dx > dy * 1.5 → side_by_side
        assert classify_formation(0.5, 0.2, 0.5, 0.8) == "side_by_side"

    def test_transition(self):
        from pipeline.formation import classify_formation
        # 비슷한 거리 → transition
        assert classify_formation(0.3, 0.3, 0.7, 0.7) == "transition"


class TestRallyPhase:
    def test_phase1(self):
        from pipeline.rally import _calc_phase
        assert _calc_phase(3, 4) == "phase1"

    def test_phase2(self):
        from pipeline.rally import _calc_phase
        assert _calc_phase(10, 5) == "phase2"

    def test_phase3(self):
        from pipeline.rally import _calc_phase
        assert _calc_phase(20, 15) == "phase3"

    def test_deuce(self):
        from pipeline.rally import _calc_phase
        assert _calc_phase(24, 24) == "deuce"


class TestInterpolation:
    def test_basic_interpolation(self):
        from pipeline.rally import interpolate_positions
        positions = [
            (0, 10.0, 10.0, 1.0),
            (1, 0.0, 0.0, 0.0),  # 미감지
            (2, 0.0, 0.0, 0.0),  # 미감지
            (3, 20.0, 20.0, 1.0),
        ]
        result = interpolate_positions(positions, max_gap=30)
        # 보간된 프레임의 conf=0 유지 확인
        assert result[1][3] == 0.0
        assert result[2][3] == 0.0
        # x, y는 보간되어야 함
        assert result[1][1] != 0.0
        assert result[2][1] != 0.0

    def test_no_interpolation_beyond_max_gap(self):
        from pipeline.rally import interpolate_positions
        # 31프레임 연속 미감지 → 보간 안 함
        positions = [(0, 10.0, 10.0, 1.0)]
        for i in range(1, 32):
            positions.append((i, 0.0, 0.0, 0.0))
        positions.append((32, 20.0, 20.0, 1.0))

        result = interpolate_positions(positions, max_gap=30)
        # 미감지 구간은 0.0 유지
        assert result[1][1] == 0.0


class TestScoreRally:
    def test_us_win_bonus(self):
        from pipeline.editor import score_rally
        rally = {"strokes": 5, "result": "us"}
        assert score_rally(rally) == 5 * 2 + 10  # 20

    def test_them_win(self):
        from pipeline.editor import score_rally
        rally = {"strokes": 5, "result": "them"}
        assert score_rally(rally) == 5 * 2  # 10

    def test_top3_selection(self):
        from pipeline.editor import score_rally
        rallies = [
            {"id": 1, "strokes": 3, "result": "us"},   # 16
            {"id": 2, "strokes": 10, "result": "them"}, # 20
            {"id": 3, "strokes": 8, "result": "us"},    # 26
            {"id": 4, "strokes": 1, "result": "us"},    # 12
            {"id": 5, "strokes": 7, "result": "them"},  # 14
        ]
        top3 = sorted(rallies, key=score_rally, reverse=True)[:3]
        top3_ids = {r["id"] for r in top3}
        assert top3_ids == {1, 2, 3}  # 26, 20, 16

    def test_neutral_result_no_bonus(self):
        from pipeline.editor import score_rally
        rally = {"strokes": 5, "result": "neutral"}
        assert score_rally(rally) == 5 * 2  # bonus 없음

    def test_fewer_than_3_rallies_returns_all(self):
        from pipeline.editor import score_rally
        rallies = [
            {"id": 1, "strokes": 5, "result": "us"},
            {"id": 2, "strokes": 3, "result": "them"},
        ]
        top3 = sorted(rallies, key=score_rally, reverse=True)[:3]
        assert len(top3) == 2  # 2개만 있으면 2개 반환

    def test_zero_strokes_rally(self):
        from pipeline.editor import score_rally
        rally = {"strokes": 0, "result": "us"}
        assert score_rally(rally) == 10  # 0 * 2 + 10


class TestInterpolationEdgeCases:
    def test_empty_positions_returns_empty(self):
        from pipeline.rally import interpolate_positions
        assert interpolate_positions([], max_gap=30) == []

    def test_single_detected_no_change(self):
        from pipeline.rally import interpolate_positions
        positions = [(0, 5.0, 5.0, 1.0)]
        result = interpolate_positions(positions, max_gap=30)
        assert result == positions

    def test_gap_at_start_not_interpolated(self):
        """앞에 감지된 프레임 없으면 보간 불가 → 0.0 유지"""
        from pipeline.rally import interpolate_positions
        positions = [
            (0, 0.0, 0.0, 0.0),  # 미감지 (이전 프레임 없음)
            (1, 10.0, 10.0, 1.0),
        ]
        result = interpolate_positions(positions, max_gap=30)
        assert result[0][1] == 0.0  # 보간 불가

    def test_gap_at_end_not_interpolated(self):
        """뒤에 감지된 프레임 없으면 보간 불가 → 0.0 유지"""
        from pipeline.rally import interpolate_positions
        positions = [
            (0, 10.0, 10.0, 1.0),
            (1, 0.0, 0.0, 0.0),  # 미감지 (이후 프레임 없음)
        ]
        result = interpolate_positions(positions, max_gap=30)
        assert result[1][1] == 0.0

    def test_exactly_max_gap_is_interpolated(self):
        """정확히 max_gap=30 프레임 → 보간됨"""
        from pipeline.rally import interpolate_positions
        positions = [(0, 0.0, 0.0, 1.0)]
        for i in range(1, 31):
            positions.append((i, 0.0, 0.0, 0.0))
        positions.append((31, 30.0, 30.0, 1.0))
        result = interpolate_positions(positions, max_gap=30)
        assert result[1][1] != 0.0  # 보간됨

    def test_over_max_gap_not_interpolated(self):
        """31프레임 미감지 → 보간 안 됨"""
        from pipeline.rally import interpolate_positions
        positions = [(0, 0.0, 0.0, 1.0)]
        for i in range(1, 32):
            positions.append((i, 0.0, 0.0, 0.0))
        positions.append((32, 30.0, 30.0, 1.0))
        result = interpolate_positions(positions, max_gap=30)
        assert result[1][1] == 0.0  # 보간 안 됨


class TestCalcPhaseEdgeCases:
    def test_24_23_is_phase3(self):
        """24-23: 한쪽만 24 → 듀스 아님, phase3"""
        from pipeline.rally import _calc_phase
        assert _calc_phase(24, 23) == "phase3"

    def test_23_24_is_phase3(self):
        from pipeline.rally import _calc_phase
        assert _calc_phase(23, 24) == "phase3"

    def test_0_0_is_phase1(self):
        from pipeline.rally import _calc_phase
        assert _calc_phase(0, 0) == "phase1"

    def test_17_17_is_phase2(self):
        from pipeline.rally import _calc_phase
        assert _calc_phase(17, 17) == "phase2"

    def test_18_0_is_phase3(self):
        from pipeline.rally import _calc_phase
        assert _calc_phase(18, 0) == "phase3"


class TestProgressSync:
    """파이프라인 진행률 동기화 테스트 — _push_progress가 jobs dict와 WS 모두 업데이트하는지 확인"""

    def test_push_progress_updates_jobs_dict(self):
        """_push_progress 호출 시 jobs[job_id]의 progress/step/status가 업데이트돼야 한다"""
        from pipeline import _push_progress

        jobs = {"job1": {"progress": 0, "step": "", "status": "processing", "result": None}}
        ws_subscribers = {}

        asyncio.run(_push_progress("job1", 30, "선수 추적 중...", jobs, ws_subscribers))

        assert jobs["job1"]["progress"] == 30
        assert jobs["job1"]["step"] == "선수 추적 중..."

    def test_push_progress_includes_status_in_ws_payload(self):
        """WS 구독자에게 status 필드가 포함된 payload가 전송돼야 한다"""
        from pipeline import _push_progress

        received = []

        class MockWS:
            async def send_json(self, data):
                received.append(data)

        jobs = {"job1": {"progress": 0, "step": "", "status": "processing", "result": None}}
        ws_subscribers = {"job1": [MockWS()]}

        asyncio.run(_push_progress("job1", 55, "랠리 감지 완료", jobs, ws_subscribers))

        assert len(received) == 1
        assert received[0]["progress"] == 55
        assert received[0]["step"] == "랠리 감지 완료"
        assert received[0]["status"] == "processing"

    def test_push_progress_removes_dead_ws(self):
        """send_json 실패한 WS는 subscribers에서 제거돼야 한다"""
        from pipeline import _push_progress

        class DeadWS:
            async def send_json(self, data):
                raise RuntimeError("연결 끊김")

        jobs = {"job1": {"progress": 0, "step": "", "status": "processing", "result": None}}
        dead = DeadWS()
        ws_subscribers = {"job1": [dead]}

        asyncio.run(_push_progress("job1", 10, "코트 감지", jobs, ws_subscribers))

        assert dead not in ws_subscribers["job1"]

    def test_progress_monotonically_increases_through_steps(self):
        """파이프라인 6단계의 progress 값이 단조 증가해야 한다"""
        from pipeline import STEPS

        values = [p for p, _ in STEPS]
        assert values == sorted(values), "progress 값이 단조 증가하지 않음"
        assert values[0] > 0
        assert values[-1] == 100

    def test_optical_flow_zero_rallies_returns_mock(self):
        """광학 플로우가 0개 랠리 반환 시 mock 랠리로 대체돼야 한다"""
        from unittest.mock import patch, MagicMock
        from pipeline.rally import detect_rallies

        court_data = {"corners": [], "homography": [], "frame_size": [1920, 1080]}

        with patch("pipeline.rally._run_tracknet", side_effect=FileNotFoundError("no model")), \
             patch("pipeline.rally._optical_flow_fallback", return_value=[]), \
             patch("pipeline.rally._split_rallies", return_value=[]), \
             patch("pipeline.rally._mock_rallies") as mock_fn:
            mock_fn.return_value = [{"id": 1}]
            result = detect_rallies("fake.mp4", court_data)

        mock_fn.assert_called_once()
        assert result == [{"id": 1}]
