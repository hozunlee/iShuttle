/**
 * jobStore.ts 단위 테스트 — RED
 */
import { describe, it, expect, beforeEach } from "vitest";
import { useJobStore } from "../store/jobStore";
import type { RallyReport } from "../types/api";

const MOCK_REPORT: RallyReport = {
  game_id: "test-game-id",
  rule: { mode: "amateur", win_score: 25, deuce_trigger: 24, deuce_cap: 31, court_change_at: 13 },
  score: { us: 15, them: 10 },
  rallies: [],
  heatmap_url: "/static/heatmap/test.png",
  pose_summary: { shoulder_rotation_avg: 45, spine_tilt_avg: 15, knee_bend_avg: 130, confidence: "high" },
  ai_report: { summary: "good game", pros: "nice", cons: ["a", "b"], focus: "next" },
};

describe("useJobStore", () => {
  beforeEach(() => {
    useJobStore.getState().reset();
  });

  describe("초기 상태", () => {
    it("jobId는 null", () => {
      expect(useJobStore.getState().jobId).toBeNull();
    });

    it("progress는 0", () => {
      expect(useJobStore.getState().progress).toBe(0);
    });

    it("status는 idle", () => {
      expect(useJobStore.getState().status).toBe("idle");
    });

    it("result는 null", () => {
      expect(useJobStore.getState().result).toBeNull();
    });

    it("errorMessage는 빈 문자열", () => {
      expect(useJobStore.getState().errorMessage).toBe("");
    });
  });

  describe("setJob", () => {
    it("jobId 설정", () => {
      useJobStore.getState().setJob("job-abc");
      expect(useJobStore.getState().jobId).toBe("job-abc");
    });

    it("status가 processing으로 변경", () => {
      useJobStore.getState().setJob("job-abc");
      expect(useJobStore.getState().status).toBe("processing");
    });

    it("progress가 0으로 리셋", () => {
      useJobStore.getState().updateProgress(50, "중간");
      useJobStore.getState().setJob("new-job");
      expect(useJobStore.getState().progress).toBe(0);
    });
  });

  describe("updateProgress", () => {
    it("progress 업데이트", () => {
      useJobStore.getState().setJob("job-1");
      useJobStore.getState().updateProgress(42, "선수 추적 중");
      expect(useJobStore.getState().progress).toBe(42);
    });

    it("step 업데이트", () => {
      useJobStore.getState().setJob("job-1");
      useJobStore.getState().updateProgress(42, "선수 추적 중");
      expect(useJobStore.getState().step).toBe("선수 추적 중");
    });
  });

  describe("setDone", () => {
    it("status가 done으로 변경", () => {
      useJobStore.getState().setDone(MOCK_REPORT);
      expect(useJobStore.getState().status).toBe("done");
    });

    it("result 저장", () => {
      useJobStore.getState().setDone(MOCK_REPORT);
      expect(useJobStore.getState().result).toEqual(MOCK_REPORT);
    });

    it("progress가 100", () => {
      useJobStore.getState().setDone(MOCK_REPORT);
      expect(useJobStore.getState().progress).toBe(100);
    });
  });

  describe("setError", () => {
    it("status가 error로 변경", () => {
      useJobStore.getState().setError("파이프라인 실패");
      expect(useJobStore.getState().status).toBe("error");
    });

    it("errorMessage 저장", () => {
      useJobStore.getState().setError("파이프라인 실패");
      expect(useJobStore.getState().errorMessage).toBe("파이프라인 실패");
    });
  });

  describe("reset", () => {
    it("완료 상태에서 reset → idle", () => {
      useJobStore.getState().setDone(MOCK_REPORT);
      useJobStore.getState().reset();
      expect(useJobStore.getState().status).toBe("idle");
    });

    it("reset 후 result는 null", () => {
      useJobStore.getState().setDone(MOCK_REPORT);
      useJobStore.getState().reset();
      expect(useJobStore.getState().result).toBeNull();
    });

    it("reset 후 progress는 0", () => {
      useJobStore.getState().updateProgress(70, "자세 분석 중");
      useJobStore.getState().reset();
      expect(useJobStore.getState().progress).toBe(0);
    });

    it("reset 후 jobId는 null", () => {
      useJobStore.getState().setJob("some-job");
      useJobStore.getState().reset();
      expect(useJobStore.getState().jobId).toBeNull();
    });
  });
});
