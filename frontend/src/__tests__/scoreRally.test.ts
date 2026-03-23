/**
 * CONTEXT.md TOP3 선정 공식 & 게임 phase 로직 프론트엔드 단위 테스트
 *
 * 백엔드 score_rally / _calc_phase와 동일한 로직을 FE에서도 검증.
 * utils/rally.ts가 생성될 예정 → 현재 RED
 */
import { describe, it, expect } from "vitest";
import { scoreRally, getTop3Rallies, calcPhase } from "../utils/rally";
import type { Rally } from "../types/api";

const makeRally = (id: number, strokes: number, result: "us" | "them" | "neutral"): Rally => ({
  id,
  timestamp: { start_sec: 0, end_sec: 10 },
  strokes,
  result,
  score_at_end: { us: 0, them: 0 },
  phase: "phase1",
  formation: { dominant: "front_back", transitions: 0 },
  clip_url: "",
  short_url: "",
  detection_gaps: [],
});

describe("scoreRally", () => {
  it("us 득점: strokes*2 + 10", () => {
    expect(scoreRally(makeRally(1, 5, "us"))).toBe(20);
  });

  it("them 득점: strokes*2", () => {
    expect(scoreRally(makeRally(1, 5, "them"))).toBe(10);
  });

  it("neutral: strokes*2", () => {
    expect(scoreRally(makeRally(1, 5, "neutral"))).toBe(10);
  });

  it("0타 us 득점: 0*2 + 10 = 10", () => {
    expect(scoreRally(makeRally(1, 0, "us"))).toBe(10);
  });
});

describe("getTop3Rallies", () => {
  it("5개 중 상위 3개 반환", () => {
    const rallies = [
      makeRally(1, 3, "us"),   // 16
      makeRally(2, 10, "them"), // 20
      makeRally(3, 8, "us"),   // 26
      makeRally(4, 1, "us"),   // 12
      makeRally(5, 7, "them"), // 14
    ];
    const top3 = getTop3Rallies(rallies);
    const ids = top3.map((r) => r.id);
    expect(ids).toContain(3); // 26
    expect(ids).toContain(2); // 20
    expect(ids).toContain(1); // 16
    expect(top3).toHaveLength(3);
  });

  it("2개면 2개 반환", () => {
    const rallies = [makeRally(1, 5, "us"), makeRally(2, 3, "them")];
    expect(getTop3Rallies(rallies)).toHaveLength(2);
  });

  it("빈 배열이면 빈 배열 반환", () => {
    expect(getTop3Rallies([])).toHaveLength(0);
  });

  it("내림차순 정렬", () => {
    const rallies = [makeRally(1, 3, "us"), makeRally(2, 8, "us"), makeRally(3, 1, "us")];
    const top3 = getTop3Rallies(rallies);
    expect(top3[0].id).toBe(2); // 26
    expect(top3[1].id).toBe(1); // 16
    expect(top3[2].id).toBe(3); // 12
  });
});

describe("calcPhase", () => {
  it("0-0 → phase1", () => {
    expect(calcPhase(0, 0)).toBe("phase1");
  });

  it("8-5 → phase1", () => {
    expect(calcPhase(8, 5)).toBe("phase1");
  });

  it("9-0 → phase2", () => {
    expect(calcPhase(9, 0)).toBe("phase2");
  });

  it("10-5 → phase2", () => {
    expect(calcPhase(10, 5)).toBe("phase2");
  });

  it("18-10 → phase3", () => {
    expect(calcPhase(18, 10)).toBe("phase3");
  });

  it("24-24 → deuce", () => {
    expect(calcPhase(24, 24)).toBe("deuce");
  });

  it("24-23 → phase3 (한쪽만 24, 듀스 아님)", () => {
    expect(calcPhase(24, 23)).toBe("phase3");
  });
});
