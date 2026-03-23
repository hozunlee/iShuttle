"""
reporter.py — Claude API 기반 게임 리포트 & 피드백 생성

- 모델: claude-sonnet-4-6
- 폴백: API 키 없거나 오류 시 룰 기반 템플릿 리포트 자동 생성
- 게임 종료 후 전체 RallyReport를 1회 전송
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger("ishuttle.pipeline.reporter")


def generate_report(game_data: dict) -> dict:
    """
    게임 데이터로 Claude API AI 리포트를 생성한다.

    Returns:
        { summary, pros, cons: list[str], focus }
    """
    logger.info("[reporter] AI 리포트 생성 시작")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("[reporter] ANTHROPIC_API_KEY 없음. 룰 기반 템플릿 사용")
        return _template_report(game_data)

    try:
        return _call_claude_api(game_data)
    except Exception as e:
        logger.error(f"[reporter] Claude API 오류: {e}. 템플릿 폴백")
        return _template_report(game_data)


async def generate_feedback(full_result: dict, selected_rallies: list[dict]) -> dict:
    """
    선택한 랠리 기반 추가 피드백을 생성한다.
    """
    logger.info(f"[reporter] 피드백 생성: {len(selected_rallies)}개 랠리 선택")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _template_report({"rallies": selected_rallies, "pose_summary": full_result.get("pose_summary", {})})

    try:
        return _call_claude_feedback(full_result, selected_rallies)
    except Exception as e:
        logger.error(f"[reporter] 피드백 Claude API 오류: {e}")
        return _template_report({"rallies": selected_rallies, "pose_summary": full_result.get("pose_summary", {})})


def _call_claude_api(game_data: dict) -> dict:
    """Claude API로 게임 리포트 생성"""
    import anthropic

    client = anthropic.Anthropic()
    rallies = game_data.get("rallies", [])
    pose = game_data.get("pose_summary", {})
    game_config = game_data.get("game_config", {})

    rally_count = len(rallies)
    avg_strokes = sum(r.get("strokes", 0) for r in rallies) / max(rally_count, 1)
    us_rallies = [r for r in rallies if r.get("result") == "us"]
    them_rallies = [r for r in rallies if r.get("result") == "them"]

    formation_counts: dict[str, int] = {}
    for r in rallies:
        f = r.get("formation", {}).get("dominant", "transition")
        formation_counts[f] = formation_counts.get(f, 0) + 1

    formation_pct = {k: round(v / max(rally_count, 1) * 100) for k, v in formation_counts.items()}

    prompt = f"""
배드민턴 복식 동호인 게임 분석 데이터:
- 최종 스코어: 우리팀 {len(us_rallies)} : 상대팀 {len(them_rallies)}
- 총 랠리: {rally_count}개, 평균 {avg_strokes:.1f}타
- 포메이션 비율: 전후 {formation_pct.get('front_back', 0)}% / 좌우 {formation_pct.get('side_by_side', 0)}% / 과도기 {formation_pct.get('transition', 0)}%
- 자세 데이터: 어깨회전 {pose.get('shoulder_rotation_avg', 0)}도 / 척추기울기 {pose.get('spine_tilt_avg', 0)}도 / 무릎굽힘 {pose.get('knee_bend_avg', 0)}도 (신뢰도: {pose.get('confidence', 'low')})

아래 형식으로 한국어 코칭 피드백을 작성해라:
1. 총평 (2문장)
2. 잘한 점 1가지
3. 개선할 점 2가지 (구체적으로)
4. 다음 게임 집중 포인트 1가지

JSON으로만 응답. 키: summary, pros, cons(배열), focus
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    # JSON 파싱 (마크다운 코드블록 제거)
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def _call_claude_feedback(full_result: dict, selected_rallies: list[dict]) -> dict:
    """선택 랠리 기반 Claude API 피드백"""
    import anthropic

    client = anthropic.Anthropic()

    rally_summary = "\n".join(
        f"- 랠리 {r['id']}: {r['strokes']}타, 결과={r.get('result')}, 포메이션={r.get('formation', {}).get('dominant')}"
        for r in selected_rallies
    )

    prompt = f"""
다음 배드민턴 랠리들에 대한 집중 분석을 해줘:
{rally_summary}

JSON으로만 응답. 키: summary, pros, cons(배열), focus
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def _template_report(game_data: dict) -> dict:
    """API 키 없거나 오류 시 룰 기반 템플릿 리포트"""
    rallies = game_data.get("rallies", [])
    pose = game_data.get("pose_summary", {})

    rally_count = len(rallies)
    us_count = sum(1 for r in rallies if r.get("result") == "us")
    them_count = sum(1 for r in rallies if r.get("result") == "them")
    avg_strokes = sum(r.get("strokes", 0) for r in rallies) / max(rally_count, 1)

    win = us_count > them_count

    summary = (
        f"총 {rally_count}개의 랠리 중 우리팀이 {us_count}점을 득점했습니다. "
        + ("전반적으로 안정적인 경기 운영을 보여줬습니다." if win else "상대팀에게 아쉽게 패배했지만 개선할 점이 있습니다.")
    )

    pros = f"평균 {avg_strokes:.1f}타의 랠리를 이어가며 안정적인 경기력을 보여줬습니다."

    cons = [
        "포메이션 전환 시 중앙 공간이 노출되는 구간을 줄여야 합니다.",
        "서브 득점 패턴을 다양화하여 상대방의 예측을 어렵게 하세요.",
    ]

    focus = "다음 게임에서는 전후 포메이션 유지 시간을 늘려 공격 기회를 만들어보세요."

    return {
        "summary": summary,
        "pros": pros,
        "cons": cons,
        "focus": focus,
    }
