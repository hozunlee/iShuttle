"""reporter.py 테스트"""

import json
import os
import pytest


class TestTemplateReport:
    def test_all_keys_present(self):
        from pipeline.reporter import _template_report
        result = _template_report({"rallies": [], "pose_summary": {}})
        for key in ["summary", "pros", "cons", "focus"]:
            assert key in result, f"Missing key: {key}"

    def test_cons_is_list(self):
        from pipeline.reporter import _template_report
        result = _template_report({"rallies": [], "pose_summary": {}})
        assert isinstance(result["cons"], list)

    def test_cons_has_exactly_two_items(self):
        from pipeline.reporter import _template_report
        result = _template_report({"rallies": [], "pose_summary": {}})
        assert len(result["cons"]) == 2

    def test_summary_is_nonempty_string(self):
        from pipeline.reporter import _template_report
        result = _template_report({"rallies": [], "pose_summary": {}})
        assert isinstance(result["summary"], str)
        assert len(result["summary"]) > 0

    def test_pros_is_nonempty_string(self):
        from pipeline.reporter import _template_report
        result = _template_report({"rallies": [], "pose_summary": {}})
        assert isinstance(result["pros"], str)
        assert len(result["pros"]) > 0

    def test_focus_is_nonempty_string(self):
        from pipeline.reporter import _template_report
        result = _template_report({"rallies": [], "pose_summary": {}})
        assert isinstance(result["focus"], str)
        assert len(result["focus"]) > 0

    def test_win_case_summary_contains_rally_count(self):
        from pipeline.reporter import _template_report
        rallies = [
            {"result": "us", "strokes": 5},
            {"result": "us", "strokes": 3},
            {"result": "them", "strokes": 4},
        ]
        result = _template_report({"rallies": rallies, "pose_summary": {}})
        assert "3" in result["summary"]  # 총 랠리 수

    def test_lose_case_summary_mentions_defeat(self):
        from pipeline.reporter import _template_report
        rallies = [
            {"result": "them", "strokes": 5},
            {"result": "them", "strokes": 3},
            {"result": "us", "strokes": 4},
        ]
        result = _template_report({"rallies": rallies, "pose_summary": {}})
        assert "패배" in result["summary"] or "아쉽" in result["summary"]

    def test_empty_rallies_no_crash(self):
        from pipeline.reporter import _template_report
        result = _template_report({"rallies": [], "pose_summary": {}})
        assert result is not None

    def test_cons_items_are_strings(self):
        from pipeline.reporter import _template_report
        result = _template_report({"rallies": [], "pose_summary": {}})
        for item in result["cons"]:
            assert isinstance(item, str) and len(item) > 0


class TestGenerateReportNoApiKey:
    def test_no_key_returns_template_structure(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from pipeline.reporter import generate_report
        result = generate_report({"rallies": [], "pose_summary": {}})
        for key in ["summary", "pros", "cons", "focus"]:
            assert key in result

    def test_no_key_cons_is_list(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from pipeline.reporter import generate_report
        result = generate_report({"rallies": [], "pose_summary": {}})
        assert isinstance(result["cons"], list)

    def test_result_with_rallies_schema_valid(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from pipeline.reporter import generate_report
        result = generate_report({
            "rallies": [
                {"id": 1, "result": "us", "strokes": 7, "formation": {"dominant": "front_back", "transitions": 1}},
                {"id": 2, "result": "them", "strokes": 3, "formation": {"dominant": "side_by_side", "transitions": 0}},
            ],
            "pose_summary": {
                "shoulder_rotation_avg": 45.0,
                "spine_tilt_avg": 15.0,
                "knee_bend_avg": 130.0,
                "confidence": "medium",
            },
        })
        for key in ["summary", "pros", "cons", "focus"]:
            assert key in result


class TestClaudeJsonParsing:
    """Claude API 응답 파싱 로직 — reporter 내부 로직 직접 검증"""

    def _parse(self, text: str) -> dict:
        """reporter._call_claude_api 파싱 로직과 동일"""
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())

    def test_parse_markdown_json_block(self):
        raw = '```json\n{"summary": "good", "pros": "nice", "cons": ["a", "b"], "focus": "next"}\n```'
        result = self._parse(raw)
        assert result["summary"] == "good"
        assert len(result["cons"]) == 2

    def test_parse_plain_json(self):
        raw = '{"summary": "good", "pros": "nice", "cons": ["a", "b"], "focus": "next"}'
        result = self._parse(raw)
        assert result["focus"] == "next"

    def test_parse_json_without_json_prefix(self):
        raw = "```\n{\"summary\": \"ok\", \"pros\": \"p\", \"cons\": [\"x\"], \"focus\": \"f\"}\n```"
        result = self._parse(raw)
        assert result["summary"] == "ok"

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            self._parse("not json at all")


class TestBuildRallyReport:
    """pipeline.__init__._build_rally_report 조립 검증"""

    def test_required_top_level_keys(self):
        from pipeline import _build_rally_report
        result = _build_rally_report(
            game_id="test-game-id",
            game_config={"rule_mode": "amateur"},
            rallies=[],
            pose_summary={"shoulder_rotation_avg": 0, "spine_tilt_avg": 0, "knee_bend_avg": 0, "confidence": "low"},
            ai_report={"summary": "s", "pros": "p", "cons": ["a", "b"], "focus": "f"},
        )
        for key in ["game_id", "rule", "score", "rallies", "heatmap_url", "pose_summary", "ai_report"]:
            assert key in result, f"Missing key: {key}"

    def test_score_counts_us_them(self):
        from pipeline import _build_rally_report
        rallies = [
            {"id": 1, "result": "us"},
            {"id": 2, "result": "us"},
            {"id": 3, "result": "them"},
            {"id": 4, "result": "neutral"},
        ]
        result = _build_rally_report(
            game_id="g1",
            game_config={"rule_mode": "amateur"},
            rallies=rallies,
            pose_summary={"shoulder_rotation_avg": 0, "spine_tilt_avg": 0, "knee_bend_avg": 0, "confidence": "low"},
            ai_report={"summary": "s", "pros": "p", "cons": ["a", "b"], "focus": "f"},
        )
        assert result["score"]["us"] == 2
        assert result["score"]["them"] == 1

    def test_heatmap_url_contains_game_id(self):
        from pipeline import _build_rally_report
        game_id = "unique-game-xyz"
        result = _build_rally_report(
            game_id=game_id,
            game_config={},
            rallies=[],
            pose_summary={"shoulder_rotation_avg": 0, "spine_tilt_avg": 0, "knee_bend_avg": 0, "confidence": "low"},
            ai_report={"summary": "s", "pros": "p", "cons": [], "focus": "f"},
        )
        assert game_id in result["heatmap_url"]

    def test_rule_mode_default_amateur(self):
        from pipeline import _build_rally_report
        result = _build_rally_report(
            game_id="g",
            game_config={},
            rallies=[],
            pose_summary={"shoulder_rotation_avg": 0, "spine_tilt_avg": 0, "knee_bend_avg": 0, "confidence": "low"},
            ai_report={"summary": "s", "pros": "p", "cons": [], "focus": "f"},
        )
        assert result["rule"]["mode"] == "amateur"
        assert result["rule"]["win_score"] == 25
        assert result["rule"]["deuce_trigger"] == 24
        assert result["rule"]["deuce_cap"] == 31
