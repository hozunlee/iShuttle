"""
game_rules.py — 배드민턴 동호인 단판 게임 룰

CONTEXT.md 기준:
- 25점 선취 승리
- 24-24 → 듀스, 2점 차 선승
- 31점 즉시 승리 (듀스 상한)
- 13점 도달 시 코트교체 (1회)
"""

GAME_MODE = {
    "amateur": {
        "win_score": 25,
        "deuce_trigger": 24,
        "deuce_win_diff": 2,
        "deuce_cap": 31,
        "court_change_at": 13,
        "sets": 1,
    }
}


def check_winner(us: int, them: int, mode: str = "amateur") -> str | None:
    """
    현재 점수로 승자를 판단한다.

    Returns:
        'us' | 'them' | None(경기 계속)
    """
    m = GAME_MODE[mode]

    # deuce_cap 도달 → 즉시 승리
    if us >= m["deuce_cap"] or them >= m["deuce_cap"]:
        return "us" if us > them else "them"

    # 듀스 구간: 양쪽 모두 deuce_trigger 이상
    if us >= m["deuce_trigger"] and them >= m["deuce_trigger"]:
        if abs(us - them) >= m["deuce_win_diff"]:
            return "us" if us > them else "them"
        return None  # 듀스 중, 아직 2점 차 미달

    # 일반 승리 조건
    if us >= m["win_score"]:
        return "us"
    if them >= m["win_score"]:
        return "them"

    return None


def check_court_change(us: int, them: int, mode: str = "amateur") -> bool:
    """
    코트교체 발생 시점 판단.

    13점을 정확히 도달한 순간 True.
    이후 재호출 방지는 호출자 책임.
    """
    t = GAME_MODE[mode]["court_change_at"]
    return us == t or them == t
