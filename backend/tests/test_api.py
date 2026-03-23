"""FastAPI 엔드포인트 테스트 — 전부 RED (신규 파일)"""

import io
import json
import sys
import os
import uuid

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as c:
        yield c


# ─── /health ────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_has_status_ok(self, client):
        resp = client.get("/health")
        assert resp.json()["status"] == "ok"

    def test_health_has_jobs_count(self, client):
        resp = client.get("/health")
        assert "jobs" in resp.json()


# ─── POST /api/analyze ───────────────────────────────────────────────────────

class TestAnalyze:
    def _fake_video(self) -> tuple:
        return ("test.mp4", io.BytesIO(b"fake video bytes"), "video/mp4")

    def test_valid_request_returns_job_id(self, client):
        resp = client.post(
            "/api/analyze",
            data={"game_config": json.dumps({"rule_mode": "amateur"})},
            files={"video_file": self._fake_video()},
        )
        assert resp.status_code == 200
        assert "job_id" in resp.json()

    def test_valid_request_status_processing(self, client):
        resp = client.post(
            "/api/analyze",
            data={"game_config": json.dumps({"rule_mode": "amateur"})},
            files={"video_file": self._fake_video()},
        )
        assert resp.json()["status"] == "processing"

    def test_invalid_game_config_json_returns_422(self, client):
        resp = client.post(
            "/api/analyze",
            data={"game_config": "not-valid-json!!!"},
            files={"video_file": self._fake_video()},
        )
        assert resp.status_code == 422

    def test_missing_video_file_returns_422(self, client):
        resp = client.post(
            "/api/analyze",
            data={"game_config": json.dumps({"rule_mode": "amateur"})},
        )
        assert resp.status_code == 422

    def test_missing_game_config_returns_422(self, client):
        resp = client.post(
            "/api/analyze",
            files={"video_file": self._fake_video()},
        )
        assert resp.status_code == 422

    def test_job_id_is_unique_per_request(self, client):
        cfg = json.dumps({"rule_mode": "amateur"})
        r1 = client.post("/api/analyze", data={"game_config": cfg}, files={"video_file": self._fake_video()})
        r2 = client.post("/api/analyze", data={"game_config": cfg}, files={"video_file": self._fake_video()})
        assert r1.json()["job_id"] != r2.json()["job_id"]


# ─── GET /api/status/{job_id} ────────────────────────────────────────────────

class TestStatus:
    def test_unknown_job_id_returns_404(self, client):
        resp = client.get("/api/status/unknown-job-id-xyz")
        assert resp.status_code == 404

    def test_existing_job_has_progress_field(self, client):
        job_id = self._create_job(client)
        resp = client.get(f"/api/status/{job_id}")
        assert resp.status_code == 200
        assert "progress" in resp.json()

    def test_existing_job_has_step_field(self, client):
        job_id = self._create_job(client)
        resp = client.get(f"/api/status/{job_id}")
        assert "step" in resp.json()

    def test_existing_job_has_status_field(self, client):
        job_id = self._create_job(client)
        resp = client.get(f"/api/status/{job_id}")
        assert "status" in resp.json()

    def test_initial_progress_is_valid_range(self, client):
        """BackgroundTask가 동기 실행될 수 있으므로 0~100 범위 확인"""
        job_id = self._create_job(client)
        resp = client.get(f"/api/status/{job_id}")
        assert 0 <= resp.json()["progress"] <= 100

    def _create_job(self, client) -> str:
        resp = client.post(
            "/api/analyze",
            data={"game_config": json.dumps({"rule_mode": "amateur"})},
            files={"video_file": ("t.mp4", io.BytesIO(b"x"), "video/mp4")},
        )
        return resp.json()["job_id"]


# ─── GET /api/results/{job_id} ───────────────────────────────────────────────

class TestResults:
    def _mock_result(self, game_id: str) -> dict:
        return {
            "game_id": game_id,
            "rule": {"mode": "amateur", "win_score": 25, "deuce_trigger": 24, "deuce_cap": 31, "court_change_at": 13},
            "score": {"us": 15, "them": 10},
            "rallies": [],
            "heatmap_url": f"/static/heatmap/{game_id}.png",
            "pose_summary": {"shoulder_rotation_avg": 45.0, "spine_tilt_avg": 15.0, "knee_bend_avg": 130.0, "confidence": "high"},
            "ai_report": {"summary": "test", "pros": "good", "cons": ["a", "b"], "focus": "next"},
        }

    def test_unknown_job_returns_404(self, client):
        resp = client.get("/api/results/unknown-id-xyz")
        assert resp.status_code == 404

    def test_processing_job_returns_202(self, client):
        job_id = str(uuid.uuid4())
        client.app.state.jobs[job_id] = {
            "progress": 30,
            "step": "선수 추적 중...",
            "status": "processing",
            "result": None,
        }
        resp = client.get(f"/api/results/{job_id}")
        assert resp.status_code == 202

    def test_error_job_returns_500(self, client):
        job_id = str(uuid.uuid4())
        client.app.state.jobs[job_id] = {
            "progress": 30,
            "step": "오류 발생",
            "status": "error",
            "result": None,
        }
        resp = client.get(f"/api/results/{job_id}")
        assert resp.status_code == 500

    def test_done_job_returns_rally_report(self, client):
        game_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        client.app.state.jobs[job_id] = {
            "progress": 100,
            "step": "완료",
            "status": "done",
            "result": self._mock_result(game_id),
        }
        resp = client.get(f"/api/results/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["game_id"] == game_id

    def test_done_result_has_required_keys(self, client):
        game_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        client.app.state.jobs[job_id] = {
            "progress": 100,
            "step": "완료",
            "status": "done",
            "result": self._mock_result(game_id),
        }
        resp = client.get(f"/api/results/{job_id}")
        data = resp.json()
        for key in ["game_id", "rule", "score", "rallies", "heatmap_url", "pose_summary", "ai_report"]:
            assert key in data, f"Missing key: {key}"


# ─── POST /api/feedback ──────────────────────────────────────────────────────

class TestFeedback:
    def _register_done_job(self, client, rallies: list) -> str:
        game_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        client.app.state.jobs[job_id] = {
            "progress": 100,
            "step": "완료",
            "status": "done",
            "result": {
                "game_id": game_id,
                "rallies": rallies,
                "pose_summary": {"shoulder_rotation_avg": 45.0, "spine_tilt_avg": 0.0, "knee_bend_avg": 130.0, "confidence": "low"},
            },
        }
        return game_id

    def test_game_not_found_returns_404(self, client):
        resp = client.post("/api/feedback", json={"game_id": "no-such-game", "rally_ids": [1]})
        assert resp.status_code == 404

    def test_no_matching_rallies_returns_422(self, client):
        game_id = self._register_done_job(client, [{"id": 1, "strokes": 5, "result": "us"}])
        resp = client.post("/api/feedback", json={"game_id": game_id, "rally_ids": [999]})
        assert resp.status_code == 422

    def test_valid_feedback_returns_required_keys(self, client):
        rallies = [{"id": 1, "strokes": 7, "result": "us"}, {"id": 2, "strokes": 4, "result": "them"}]
        game_id = self._register_done_job(client, rallies)
        resp = client.post("/api/feedback", json={"game_id": game_id, "rally_ids": [1]})
        assert resp.status_code == 200
        data = resp.json()
        for key in ["summary", "pros", "cons", "focus"]:
            assert key in data, f"Missing key: {key}"

    def test_feedback_cons_is_list(self, client):
        rallies = [{"id": 1, "strokes": 5, "result": "us"}]
        game_id = self._register_done_job(client, rallies)
        resp = client.post("/api/feedback", json={"game_id": game_id, "rally_ids": [1]})
        assert resp.status_code == 200
        assert isinstance(resp.json()["cons"], list)

    def test_missing_rally_ids_field_returns_422(self, client):
        resp = client.post("/api/feedback", json={"game_id": "some-id"})
        assert resp.status_code == 422

    def test_missing_game_id_field_returns_422(self, client):
        resp = client.post("/api/feedback", json={"rally_ids": [1]})
        assert resp.status_code == 422
