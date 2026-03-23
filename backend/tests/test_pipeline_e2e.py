"""
test_pipeline_e2e.py — fallback 체인 end-to-end RED 테스트

실제 영상/모델 없이 mock 데이터로 전체 파이프라인이 에러 없이 완주하는지 검증.
"""

import os
import sys
import asyncio
import tempfile
import pytest
import unittest.mock as mock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def dummy_video(tmp_path):
    """빈 더미 영상 파일 경로"""
    f = tmp_path / "dummy.mp4"
    f.write_bytes(b"\x00" * 100)
    return str(f)


@pytest.fixture
def game_config():
    return {"rule_mode": "amateur"}


class TestPipelineFallbackChain:
    """각 단계가 fallback으로 mock 데이터를 반환하는지 검증"""

    def test_court_fallback_returns_required_keys(self, dummy_video):
        """court.py fallback은 corners, homography, frame_size 반환"""
        from pipeline.court import _fallback_court
        result = _fallback_court(dummy_video)
        assert "corners" in result
        assert "homography" in result
        assert "frame_size" in result
        assert len(result["corners"]) == 4

    def test_tracker_fallback_returns_4_players(self, dummy_video):
        """tracker.py fallback은 4명 선수 데이터 반환"""
        from pipeline.tracker import _fallback_tracks
        court = {"corners": [], "homography": [], "frame_size": [1920, 1080]}
        result = _fallback_tracks(dummy_video)
        assert "players" in result
        assert len(result["players"]) == 4
        assert "fps" in result
        assert "total_frames" in result

    def test_rally_mock_returns_list_with_required_keys(self, dummy_video):
        """rally.py mock fallback은 랠리 리스트 반환, 각 항목에 필수 키 존재"""
        import cv2
        from pipeline.rally import _mock_rallies

        with mock.patch("cv2.VideoCapture") as mock_cap_cls:
            instance = mock.MagicMock()
            instance.get.side_effect = lambda prop: {
                cv2.CAP_PROP_FPS: 30.0,
                cv2.CAP_PROP_FRAME_COUNT: 1800,
            }.get(prop, 0)
            instance.release.return_value = None
            mock_cap_cls.return_value = instance

            rallies = _mock_rallies(dummy_video)

        assert isinstance(rallies, list)
        assert len(rallies) > 0
        for r in rallies:
            for key in ["id", "timestamp", "strokes", "result", "score_at_end", "phase"]:
                assert key in r, f"랠리에 '{key}' 키 없음"

    def test_rally_result_values_are_valid(self, dummy_video):
        """mock 랠리의 result 값이 유효한 enum이어야 함"""
        import cv2
        from pipeline.rally import _mock_rallies

        with mock.patch("cv2.VideoCapture") as mock_cap_cls:
            instance = mock.MagicMock()
            instance.get.side_effect = lambda prop: {
                cv2.CAP_PROP_FPS: 30.0,
                cv2.CAP_PROP_FRAME_COUNT: 1800,
            }.get(prop, 0)
            instance.release.return_value = None
            mock_cap_cls.return_value = instance

            rallies = _mock_rallies(dummy_video)

        valid = {"us", "them", "neutral"}
        for r in rallies:
            assert r["result"] in valid, f"유효하지 않은 result: {r['result']}"

    def test_formation_classify_all_returns_formation_field(self):
        """formation.py는 rallies에 formation 필드를 추가해야 함"""
        from pipeline.formation import classify_all_formations
        rallies = [
            {"id": 1, "timestamp": {"start_sec": 0.0, "end_sec": 5.0}, "strokes": 5,
             "result": "us", "score_at_end": {"us": 1, "them": 0}, "phase": "phase1",
             "detection_gaps": []},
        ]
        player_tracks = {
            "fps": 30.0,
            "total_frames": 150,
            "players": {
                "1": [{"frame": i, "x": 0.25, "y": 0.25, "keypoints": []} for i in range(0, 150, 3)],
                "2": [{"frame": i, "x": 0.75, "y": 0.25, "keypoints": []} for i in range(0, 150, 3)],
            },
        }
        result = classify_all_formations(rallies, player_tracks)
        assert len(result) == 1
        assert "formation" in result[0], "formation 필드 없음"
        assert "dominant" in result[0]["formation"]
        assert result[0]["formation"]["dominant"] in ("front_back", "side_by_side", "transition")

    def test_reporter_template_fallback_returns_required_keys(self):
        """reporter.py 템플릿 fallback은 summary/pros/cons/focus 반환"""
        from pipeline.reporter import _template_report
        game_data = {
            "game_config": {"rule_mode": "amateur"},
            "rallies": [{"result": "us", "strokes": 7}, {"result": "them", "strokes": 3}],
            "pose_summary": {"shoulder_rotation_avg": 45.0, "knee_bend_avg": 130.0, "confidence": "medium"},
        }
        result = _template_report(game_data)
        for key in ["summary", "pros", "cons", "focus"]:
            assert key in result, f"'{key}' 키 없음"
        assert isinstance(result["cons"], list)


class TestPipelineE2ERunPipeline:
    """run_pipeline 전체 async 실행 — fallback 체인 완주"""

    def test_run_pipeline_completes_without_error(self, dummy_video, game_config, tmp_path):
        """
        TrackNetV3/YOLO/MediaPipe 없이 fallback 체인으로
        run_pipeline이 status=done 또는 error로 완주해야 함.
        (crash/unhandled exception 없어야 함)
        """
        import cv2

        jobs = {}
        ws_subscribers = {}

        # cv2.VideoCapture mock — dummy 파일을 열 수 있도록
        orig_vc = cv2.VideoCapture

        def mock_vc(path):
            cap = orig_vc.__new__(orig_vc)
            return cap

        with mock.patch("cv2.VideoCapture") as mock_cap_cls:
            instance = mock.MagicMock()
            instance.isOpened.return_value = True
            instance.get.side_effect = lambda prop: {
                cv2.CAP_PROP_FPS: 30.0,
                cv2.CAP_PROP_FRAME_COUNT: 900,
                cv2.CAP_PROP_FRAME_WIDTH: 1920,
                cv2.CAP_PROP_FRAME_HEIGHT: 1080,
            }.get(prop, 0)
            instance.read.return_value = (False, None)
            instance.release.return_value = None
            mock_cap_cls.return_value = instance

            from pipeline import run_pipeline
            import uuid
            job_id = str(uuid.uuid4())
            jobs[job_id] = {"progress": 0, "step": "", "status": "processing", "result": None}

            asyncio.run(run_pipeline(job_id, dummy_video, game_config, jobs, ws_subscribers))

        assert jobs[job_id]["status"] in ("done", "error"), \
            f"파이프라인이 완주하지 못함: {jobs[job_id]}"

    def test_run_pipeline_done_result_has_schema_keys(self, dummy_video, game_config):
        """status=done이면 result에 RallyReport 필수 키 존재"""
        import cv2

        jobs = {}
        ws_subscribers = {}

        with mock.patch("cv2.VideoCapture") as mock_cap_cls:
            instance = mock.MagicMock()
            instance.isOpened.return_value = True
            instance.get.side_effect = lambda prop: {
                cv2.CAP_PROP_FPS: 30.0,
                cv2.CAP_PROP_FRAME_COUNT: 900,
                cv2.CAP_PROP_FRAME_WIDTH: 1920,
                cv2.CAP_PROP_FRAME_HEIGHT: 1080,
            }.get(prop, 0)
            instance.read.return_value = (False, None)
            instance.release.return_value = None
            mock_cap_cls.return_value = instance

            from pipeline import run_pipeline
            import uuid
            job_id = str(uuid.uuid4())
            jobs[job_id] = {"progress": 0, "step": "", "status": "processing", "result": None}

            asyncio.run(run_pipeline(job_id, dummy_video, game_config, jobs, ws_subscribers))

        if jobs[job_id]["status"] == "done":
            result = jobs[job_id]["result"]
            for key in ["game_id", "rule", "score", "rallies", "heatmap_url", "pose_summary", "ai_report"]:
                assert key in result, f"RallyReport에 '{key}' 키 없음"
