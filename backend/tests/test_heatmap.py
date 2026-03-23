"""
test_heatmap.py — generate_heatmap RED 테스트

미구현 상태에서 실행하면 전부 FAIL (ImportError 또는 AssertionError)
"""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def player_tracks():
    """4명 선수 mock 트랙 데이터"""
    return {
        "fps": 30.0,
        "total_frames": 300,
        "players": {
            "1": [{"frame": i, "x": 0.25, "y": 0.25, "keypoints": []} for i in range(0, 300, 3)],
            "2": [{"frame": i, "x": 0.75, "y": 0.25, "keypoints": []} for i in range(0, 300, 3)],
            "3": [{"frame": i, "x": 0.25, "y": 0.75, "keypoints": []} for i in range(0, 300, 3)],
            "4": [{"frame": i, "x": 0.75, "y": 0.75, "keypoints": []} for i in range(0, 300, 3)],
        },
    }


@pytest.fixture
def court_data():
    return {
        "corners": [[288, 108], [1632, 108], [1632, 1026], [288, 1026]],
        "homography": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "frame_size": [1920, 1080],
    }


class TestGenerateHeatmapImport:
    def test_module_importable(self):
        """pipeline.heatmap 모듈이 존재해야 함"""
        from pipeline.heatmap import generate_heatmap  # noqa


class TestGenerateHeatmapOutput:
    def test_returns_output_path(self, player_tracks, court_data):
        """반환값이 output_path와 동일해야 함"""
        from pipeline.heatmap import generate_heatmap
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "heatmap.png")
            result = generate_heatmap(player_tracks, court_data, out)
            assert result == out

    def test_creates_png_file(self, player_tracks, court_data):
        """output_path에 PNG 파일이 실제로 생성돼야 함"""
        from pipeline.heatmap import generate_heatmap
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "heatmap.png")
            generate_heatmap(player_tracks, court_data, out)
            assert os.path.exists(out)

    def test_output_is_nonempty_file(self, player_tracks, court_data):
        """생성된 PNG 파일이 비어있지 않아야 함"""
        from pipeline.heatmap import generate_heatmap
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "heatmap.png")
            generate_heatmap(player_tracks, court_data, out)
            assert os.path.getsize(out) > 0

    def test_creates_parent_dir_if_missing(self, player_tracks, court_data):
        """output_path의 부모 디렉터리가 없어도 생성해야 함"""
        from pipeline.heatmap import generate_heatmap
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "subdir", "heatmap.png")
            generate_heatmap(player_tracks, court_data, out)
            assert os.path.exists(out)


class TestGenerateHeatmapZones:
    def test_all_zones_covered_with_spread_players(self, court_data):
        """선수가 코트 전역에 분산되면 9구역 모두 데이터 있어야 함"""
        from pipeline.heatmap import generate_heatmap, get_zone_counts
        # 9구역 전체 커버 트랙
        tracks = {
            "fps": 30.0,
            "total_frames": 90,
            "players": {
                "1": [
                    {"frame": i * 3, "x": (i % 3) * 0.4 + 0.1, "y": (i // 3) * 0.4 + 0.1, "keypoints": []}
                    for i in range(9)
                ],
            },
        }
        counts = get_zone_counts(tracks)
        assert len(counts) == 9
        assert sum(counts.values()) > 0

    def test_player_in_top_left_maps_to_zone_0(self, court_data):
        """x=0.1, y=0.1 → zone 0 (좌상단)"""
        from pipeline.heatmap import get_zone_counts
        tracks = {
            "fps": 30.0,
            "total_frames": 3,
            "players": {
                "1": [{"frame": 0, "x": 0.1, "y": 0.1, "keypoints": []}],
            },
        }
        counts = get_zone_counts(tracks)
        assert counts.get(0, 0) > 0

    def test_player_in_bottom_right_maps_to_zone_8(self, court_data):
        """x=0.9, y=0.9 → zone 8 (우하단)"""
        from pipeline.heatmap import get_zone_counts
        tracks = {
            "fps": 30.0,
            "total_frames": 3,
            "players": {
                "1": [{"frame": 0, "x": 0.9, "y": 0.9, "keypoints": []}],
            },
        }
        counts = get_zone_counts(tracks)
        assert counts.get(8, 0) > 0


class TestGenerateHeatmapEdgeCases:
    def test_empty_player_tracks(self, court_data):
        """선수 데이터 없어도 에러 없이 빈 히트맵 생성"""
        from pipeline.heatmap import generate_heatmap
        tracks = {"fps": 30.0, "total_frames": 0, "players": {}}
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "empty.png")
            generate_heatmap(tracks, court_data, out)
            assert os.path.exists(out)

    def test_single_frame_single_player(self, court_data):
        """프레임 1개, 선수 1명도 처리 가능"""
        from pipeline.heatmap import generate_heatmap
        tracks = {
            "fps": 30.0,
            "total_frames": 1,
            "players": {
                "1": [{"frame": 0, "x": 0.5, "y": 0.5, "keypoints": []}],
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "single.png")
            generate_heatmap(tracks, court_data, out)
            assert os.path.exists(out)
