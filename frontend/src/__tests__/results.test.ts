/**
 * FE_003 — Results 화면 렌더링 로직 테스트
 * - 포메이션 통계 퍼센트 계산
 * - 랠리 0개 처리 (division by zero 방지)
 * - 스코어 결과 라벨 (승리/무승부/패배)
 * - 랠리 필터 & 정렬
 */
import { describe, it, expect } from "vitest";
import type { Rally } from "../types/api";

// ──────────────────────────────────────────────
// 포메이션 퍼센트 계산 (HeatmapView 로직)
// ──────────────────────────────────────────────

function calcFormationPct(rallies: Rally[]): Record<string, number> {
  const total = rallies.length;
  if (total === 0) return {};
  const counts = rallies.reduce(
    (acc, r) => {
      const f = r.formation.dominant;
      acc[f] = (acc[f] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );
  return Object.fromEntries(
    Object.entries(counts).map(([k, v]) => [k, Math.round((v / total) * 100)])
  );
}

// ──────────────────────────────────────────────
// 스코어 결과 라벨 (ReportCard 로직)
// ──────────────────────────────────────────────

function scoreLabel(us: number, them: number): string {
  return us > them ? "승리" : us === them ? "무승부" : "패배";
}

// ──────────────────────────────────────────────
// 랠리 필터 & 정렬 (RallyView 로직)
// ──────────────────────────────────────────────

function scoreRally(r: Rally): number {
  return r.strokes * 2 + (r.result === "us" ? 10 : 0);
}

function makeRally(
  id: number,
  result: Rally["result"],
  strokes: number,
  formation: Rally["formation"]["dominant"] = "front_back"
): Rally {
  return {
    id,
    timestamp: { start_sec: id * 10, end_sec: id * 10 + 5 },
    strokes,
    result,
    score_at_end: { us: 0, them: 0 },
    phase: "phase1",
    formation: { dominant: formation, transitions: 0 },
    clip_url: "",
    short_url: "",
    detection_gaps: [],
  };
}

// ──────────────────────────────────────────────
// 테스트
// ──────────────────────────────────────────────

describe("HeatmapView — 포메이션 퍼센트 계산", () => {
  it("랠리가 0개이면 빈 객체를 반환한다 (division by zero 방지)", () => {
    expect(calcFormationPct([])).toEqual({});
  });

  it("단일 포메이션 → 100%", () => {
    const rallies = [
      makeRally(1, "us", 5, "front_back"),
      makeRally(2, "them", 3, "front_back"),
    ];
    const pct = calcFormationPct(rallies);
    expect(pct["front_back"]).toBe(100);
  });

  it("2:1 비율 → 67%:33%", () => {
    const rallies = [
      makeRally(1, "us", 5, "front_back"),
      makeRally(2, "them", 3, "front_back"),
      makeRally(3, "us", 4, "side_by_side"),
    ];
    const pct = calcFormationPct(rallies);
    expect(pct["front_back"]).toBe(67);
    expect(pct["side_by_side"]).toBe(33);
  });

  it("퍼센트 합산이 100에 근접한다 (반올림 오차 허용 ±2)", () => {
    const rallies = [
      makeRally(1, "us", 5, "front_back"),
      makeRally(2, "them", 3, "side_by_side"),
      makeRally(3, "us", 4, "transition"),
    ];
    const pct = calcFormationPct(rallies);
    const total = Object.values(pct).reduce((a, b) => a + b, 0);
    expect(total).toBeGreaterThanOrEqual(98);
    expect(total).toBeLessThanOrEqual(102);
  });
});

describe("ReportCard — 스코어 결과 라벨", () => {
  it("우리팀 점수가 높으면 '승리'", () => {
    expect(scoreLabel(15, 10)).toBe("승리");
  });

  it("상대팀 점수가 높으면 '패배'", () => {
    expect(scoreLabel(10, 15)).toBe("패배");
  });

  it("동점이면 '무승부'", () => {
    expect(scoreLabel(12, 12)).toBe("무승부");
  });

  it("0:0도 '무승부'", () => {
    expect(scoreLabel(0, 0)).toBe("무승부");
  });
});

describe("RallyView — 랠리 필터 & 정렬", () => {
  const rallies = [
    makeRally(1, "us", 5),
    makeRally(2, "them", 3),
    makeRally(3, "us", 8),
    makeRally(4, "neutral", 2),
  ];

  it("filter=all이면 전체 반환", () => {
    const result = rallies.filter(() => true);
    expect(result.length).toBe(4);
  });

  it("filter=us이면 득점 랠리만 반환", () => {
    const result = rallies.filter((r) => r.result === "us");
    expect(result.length).toBe(2);
    expect(result.every((r) => r.result === "us")).toBe(true);
  });

  it("filter=them이면 실점 랠리만 반환", () => {
    const result = rallies.filter((r) => r.result === "them");
    expect(result.length).toBe(1);
  });

  it("sortByScore → 점수 내림차순 정렬", () => {
    const sorted = [...rallies].sort((a, b) => scoreRally(b) - scoreRally(a));
    // rally#3: 8*2+10=26, rally#1: 5*2+10=20, rally#2: 3*2=6, rally#4: 2*2=4
    expect(sorted.map((r) => r.id)).toEqual([3, 1, 2, 4]);
  });

  it("랠리 0개 상태에서 filter 결과도 0개 — 빈 상태 메시지 표시 조건", () => {
    const result = ([] as Rally[]).filter((r) => r.result === "us");
    expect(result.length).toBe(0);
  });
});
