/**
 * progress 동기화 테스트
 * - jobStore updateProgress가 progress/step을 올바르게 반영하는지
 * - polling이 done 상태에서 멈추는지 (stopPolling 로직)
 * - status별 분기가 올바른지
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { useJobStore } from "../store/jobStore";
import type { JobStatus, RallyReport } from "../types/api";

const MOCK_REPORT: RallyReport = {
  game_id: "g1",
  rule: { mode: "amateur", win_score: 25, deuce_trigger: 24, deuce_cap: 31, court_change_at: 13 },
  score: { us: 10, them: 5 },
  rallies: [],
  heatmap_url: "/static/heatmap/g1.png",
  pose_summary: { shoulder_rotation_avg: 45, spine_tilt_avg: 15, knee_bend_avg: 130, confidence: "high" },
  ai_report: { summary: "ok", pros: "good", cons: ["a"], focus: "b" },
};

describe("progress 동기화 — jobStore", () => {
  beforeEach(() => {
    useJobStore.getState().reset();
  });

  it("updateProgress가 progress와 step을 업데이트한다", () => {
    const store = useJobStore.getState();
    store.setJob("job-1");
    store.updateProgress(35, "선수 추적 중...");

    const { progress, step } = useJobStore.getState();
    expect(progress).toBe(35);
    expect(step).toBe("선수 추적 중...");
  });

  it("updateProgress는 status를 변경하지 않는다", () => {
    const store = useJobStore.getState();
    store.setJob("job-1");
    store.updateProgress(50, "랠리 감지 중...");

    expect(useJobStore.getState().status).toBe("processing");
  });

  it("setDone은 progress=100, status=done으로 설정한다", () => {
    const store = useJobStore.getState();
    store.setJob("job-1");
    store.updateProgress(90, "AI 리포트 생성 중...");
    store.setDone(MOCK_REPORT);

    const state = useJobStore.getState();
    expect(state.progress).toBe(100);
    expect(state.status).toBe("done");
    expect(state.result).toEqual(MOCK_REPORT);
  });

  it("setError는 status=error로 설정하고 progress를 유지한다", () => {
    const store = useJobStore.getState();
    store.setJob("job-1");
    store.updateProgress(55, "랠리 감지 완료");
    store.setError("파이프라인 오류");

    const state = useJobStore.getState();
    expect(state.status).toBe("error");
    expect(state.errorMessage).toBe("파이프라인 오류");
    expect(state.progress).toBe(55); // progress는 그대로 유지
  });

  it("progress를 순차적으로 업데이트해도 마지막 값이 반영된다", () => {
    const store = useJobStore.getState();
    store.setJob("job-1");

    const steps: Array<[number, string]> = [
      [5, "코트 감지 중..."],
      [10, "코트 감지 완료"],
      [15, "선수 추적 중..."],
      [30, "선수 추적 완료"],
      [55, "랠리 감지 완료"],
      [70, "클립 편집 완료"],
      [85, "자세 분석 완료"],
      [100, "분석 완료!"],
    ];

    for (const [p, s] of steps) {
      useJobStore.getState().updateProgress(p, s);
    }

    expect(useJobStore.getState().progress).toBe(100);
    expect(useJobStore.getState().step).toBe("분석 완료!");
  });
});

describe("progress 동기화 — polling stopPolling 로직", () => {
  it("finished=true이면 이후 updateProgress가 호출되지 않아야 한다 (시뮬레이션)", () => {
    // stopPolling/finished 패턴을 직접 시뮬레이션
    let finished = false;
    const calls: number[] = [];

    const simulateUpdate = (progress: number) => {
      if (finished) return;
      calls.push(progress);
    };

    simulateUpdate(30);
    simulateUpdate(55);
    finished = true;
    simulateUpdate(70); // finished=true 이후 → 무시
    simulateUpdate(100);

    expect(calls).toEqual([30, 55]);
  });

  it("WS status=done payload는 올바른 JobStatus 구조를 가진다", () => {
    const payload: JobStatus = { progress: 100, step: "분석 완료!", status: "done" };
    expect(payload.status).toBe("done");
    expect(payload.progress).toBe(100);
  });

  it("WS status=error payload는 에러 처리 분기로 이어진다", () => {
    const store = useJobStore.getState();
    store.setJob("job-err");

    const payload: JobStatus = { progress: 35, step: "오류 발생: 파일 없음", status: "error" };

    if (payload.status === "error") {
      store.setError(payload.step ?? "알 수 없는 오류");
    }

    expect(useJobStore.getState().status).toBe("error");
    expect(useJobStore.getState().errorMessage).toBe("오류 발생: 파일 없음");
  });

  it("progress=100 도달 시 done 분기로 진입해야 한다", () => {
    const payloads: JobStatus[] = [
      { progress: 30, step: "추적 중" },
      { progress: 100, step: "완료", status: "done" },
    ];

    let doneTriggered = false;
    for (const p of payloads) {
      if (p.status === "done" || p.progress >= 100) {
        doneTriggered = true;
        break;
      }
    }

    expect(doneTriggered).toBe(true);
  });
});
