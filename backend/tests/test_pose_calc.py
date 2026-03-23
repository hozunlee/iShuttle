"""pose.py 순수 수학 함수 테스트"""

import math
import pytest


class TestCalcAngle2D:
    def test_horizontal_line_is_zero(self):
        from pipeline.pose import _calc_angle_2d
        assert _calc_angle_2d((0.0, 0.0), (1.0, 0.0)) == 0.0

    def test_vertical_line_is_90(self):
        from pipeline.pose import _calc_angle_2d
        assert _calc_angle_2d((0.0, 0.0), (0.0, 1.0)) == 90.0

    def test_45_degree_diagonal(self):
        from pipeline.pose import _calc_angle_2d
        angle = _calc_angle_2d((0.0, 0.0), (1.0, 1.0))
        assert abs(angle - 45.0) < 0.01

    def test_negative_direction_same_magnitude(self):
        """방향이 반대여도 절댓값 기준으로 동일한 각도"""
        from pipeline.pose import _calc_angle_2d
        a1 = _calc_angle_2d((0.0, 0.0), (1.0, 1.0))
        a2 = _calc_angle_2d((0.0, 0.0), (-1.0, -1.0))
        assert abs(a1 - a2) < 0.01

    def test_result_range_0_to_90(self):
        """결과는 항상 0~90도 범위"""
        from pipeline.pose import _calc_angle_2d
        for x, y in [(1, 0), (0, 1), (1, 1), (-1, 1), (1, -1)]:
            angle = _calc_angle_2d((0.0, 0.0), (float(x), float(y)))
            assert 0 <= angle <= 90, f"Out of range for ({x},{y}): {angle}"


class TestCalcSpineTilt:
    def test_vertical_spine_zero_tilt(self):
        """어깨-골반이 수직으로 정렬 → 기울기 0도"""
        from pipeline.pose import _calc_spine_tilt
        result = _calc_spine_tilt((0.5, 0.2), (0.5, 0.8))
        assert result == 0.0

    def test_horizontal_spine_90_tilt(self):
        """어깨-골반이 수평 → 90도 기울기"""
        from pipeline.pose import _calc_spine_tilt
        result = _calc_spine_tilt((0.2, 0.5), (0.8, 0.5))
        assert abs(result - 90.0) < 0.01

    def test_45_degree_tilt(self):
        from pipeline.pose import _calc_spine_tilt
        result = _calc_spine_tilt((0.0, 0.0), (1.0, 1.0))
        assert abs(result - 45.0) < 0.01

    def test_result_is_non_negative(self):
        from pipeline.pose import _calc_spine_tilt
        result = _calc_spine_tilt((0.3, 0.2), (0.4, 0.8))
        assert result >= 0


class TestCalcKneeBend:
    def test_straight_leg_180(self):
        """일직선 → 180도"""
        from pipeline.pose import _calc_knee_bend
        result = _calc_knee_bend((0.5, 0.0), (0.5, 0.5), (0.5, 1.0))
        assert abs(result - 180.0) < 0.1

    def test_right_angle_90(self):
        """직각 굽힘 → 90도"""
        from pipeline.pose import _calc_knee_bend
        result = _calc_knee_bend((0.0, 0.5), (0.5, 0.5), (0.5, 1.0))
        assert abs(result - 90.0) < 0.1

    def test_zero_magnitude_returns_180(self):
        """힙과 무릎이 같은 점 → 안전 처리, 180도"""
        from pipeline.pose import _calc_knee_bend
        result = _calc_knee_bend((0.5, 0.5), (0.5, 0.5), (0.5, 1.0))
        assert result == 180.0

    def test_acute_angle_less_than_90(self):
        """심하게 구부린 무릎 → 90도 미만"""
        from pipeline.pose import _calc_knee_bend
        # hip(0,0) knee(0,1) ankle(1,1) → 약 90도 이하는 아니지만
        # hip(0,0) knee(0,1) ankle(0.1, 1) → 거의 직각
        result = _calc_knee_bend((0.0, 0.0), (0.0, 1.0), (1.0, 1.0))
        assert abs(result - 90.0) < 0.1

    def test_result_range_0_to_180(self):
        """결과는 0~180도 범위"""
        from pipeline.pose import _calc_knee_bend
        result = _calc_knee_bend((0.3, 0.2), (0.4, 0.5), (0.5, 0.8))
        assert 0.0 <= result <= 180.0


class TestFallbackPose:
    def test_fallback_has_all_keys(self):
        from pipeline.pose import _fallback_pose
        result = _fallback_pose()
        for key in ["shoulder_rotation_avg", "spine_tilt_avg", "knee_bend_avg", "confidence"]:
            assert key in result

    def test_fallback_confidence_is_low(self):
        from pipeline.pose import _fallback_pose
        assert _fallback_pose()["confidence"] == "low"

    def test_fallback_values_are_zero(self):
        from pipeline.pose import _fallback_pose
        result = _fallback_pose()
        assert result["shoulder_rotation_avg"] == 0.0
        assert result["spine_tilt_avg"] == 0.0
        assert result["knee_bend_avg"] == 0.0
