/**
 * rally.ts — CONTEXT.md TOP3 선정 공식 & 게임 페이즈 계산
 *
 * 백엔드 pipeline/editor.py, pipeline/rally.py와 동일한 로직
 */
import type { Rally } from "../types/api";

/**
 * 랠리 점수 계산 (TOP3 선정 공식)
 * score = strokes * 2 + (10 if result == "us" else 0)
 */
export function scoreRally(rally: Pick<Rally, "strokes" | "result">): number {
  return rally.strokes * 2 + (rally.result === "us" ? 10 : 0);
}

/**
 * 상위 3개 랠리 반환 (점수 내림차순)
 */
export function getTop3Rallies(rallies: Rally[]): Rally[] {
  return [...rallies].sort((a, b) => scoreRally(b) - scoreRally(a)).slice(0, 3);
}

/**
 * 게임 페이즈 계산
 * phase1: 0~8점 / phase2: 9~17점 / phase3: 18~23점 / deuce: 양쪽 24점 이상
 */
export function calcPhase(
  us: number,
  them: number
): "phase1" | "phase2" | "phase3" | "deuce" {
  if (us >= 24 && them >= 24) return "deuce";
  const max = Math.max(us, them);
  if (max >= 18) return "phase3";
  if (max >= 9) return "phase2";
  return "phase1";
}
