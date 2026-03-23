"""게임 룰 단위 테스트 — pipeline.game_rules 모듈 (미구현 → 전부 RED)"""

import pytest


class TestCheckWinner:
    def test_us_wins_normal(self):
        from pipeline.game_rules import check_winner
        assert check_winner(25, 10) == "us"

    def test_them_wins_normal(self):
        from pipeline.game_rules import check_winner
        assert check_winner(10, 25) == "them"

    def test_game_continues_low_score(self):
        from pipeline.game_rules import check_winner
        assert check_winner(5, 3) is None

    def test_game_continues_mid_score(self):
        from pipeline.game_rules import check_winner
        assert check_winner(20, 15) is None

    def test_24_23_not_deuce_not_winner(self):
        """한쪽만 24점 → 듀스 아님, 25점 미달 → None"""
        from pipeline.game_rules import check_winner
        assert check_winner(24, 23) is None

    def test_23_24_not_deuce_not_winner(self):
        from pipeline.game_rules import check_winner
        assert check_winner(23, 24) is None

    def test_deuce_24_24_no_winner(self):
        """양쪽 24점 → 듀스 진입, 아직 승자 없음"""
        from pipeline.game_rules import check_winner
        assert check_winner(24, 24) is None

    def test_deuce_25_24_no_winner(self):
        """듀스 중 1점 차 → 승자 없음 (2점차 필요)"""
        from pipeline.game_rules import check_winner
        assert check_winner(25, 24) is None

    def test_deuce_26_24_us_wins(self):
        """듀스 중 2점 차 → us 승리"""
        from pipeline.game_rules import check_winner
        assert check_winner(26, 24) == "us"

    def test_deuce_24_26_them_wins(self):
        from pipeline.game_rules import check_winner
        assert check_winner(24, 26) == "them"

    def test_deuce_27_25_us_wins(self):
        from pipeline.game_rules import check_winner
        assert check_winner(27, 25) == "us"

    def test_deuce_cap_31_30_us_wins(self):
        """31점 도달 → 즉시 승리 (deuce_cap)"""
        from pipeline.game_rules import check_winner
        assert check_winner(31, 30) == "us"

    def test_deuce_cap_30_31_them_wins(self):
        from pipeline.game_rules import check_winner
        assert check_winner(30, 31) == "them"

    def test_deuce_cap_31_29_us_wins(self):
        """31점 = 즉시 승리, 2점차 불필요"""
        from pipeline.game_rules import check_winner
        assert check_winner(31, 29) == "us"

    def test_deuce_30_28_no_winner_yet(self):
        """듀스 중 2점 차지만 30점 미달 → 계속"""
        from pipeline.game_rules import check_winner
        assert check_winner(30, 28) == "us"

    def test_zero_zero(self):
        from pipeline.game_rules import check_winner
        assert check_winner(0, 0) is None


class TestCheckCourtChange:
    def test_us_reaches_13(self):
        from pipeline.game_rules import check_court_change
        assert check_court_change(13, 5) is True

    def test_them_reaches_13(self):
        from pipeline.game_rules import check_court_change
        assert check_court_change(5, 13) is True

    def test_no_change_us_12(self):
        from pipeline.game_rules import check_court_change
        assert check_court_change(12, 5) is False

    def test_no_change_us_14(self):
        """14점 → 이미 교체 완료, 재교체 없음"""
        from pipeline.game_rules import check_court_change
        assert check_court_change(14, 5) is False

    def test_no_change_both_below_13(self):
        from pipeline.game_rules import check_court_change
        assert check_court_change(11, 11) is False

    def test_both_13_is_true(self):
        """양쪽 모두 13 → True (호출자 책임으로 중복 호출 방지)"""
        from pipeline.game_rules import check_court_change
        assert check_court_change(13, 13) is True

    def test_zero_zero(self):
        from pipeline.game_rules import check_court_change
        assert check_court_change(0, 0) is False
