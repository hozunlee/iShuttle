/**
 * gameStore.ts 단위 테스트 — RED
 */
import { describe, it, expect, beforeEach } from "vitest";
import { useGameStore } from "../store/gameStore";

describe("useGameStore", () => {
  beforeEach(() => {
    useGameStore.getState().reset();
  });

  describe("초기 상태", () => {
    it("videoFile은 null", () => {
      expect(useGameStore.getState().videoFile).toBeNull();
    });

    it("videoFileName은 빈 문자열", () => {
      expect(useGameStore.getState().videoFileName).toBe("");
    });

    it("기본 rule_mode는 amateur", () => {
      expect(useGameStore.getState().config.rule_mode).toBe("amateur");
    });

    it("기본 my_player는 A1", () => {
      expect(useGameStore.getState().config.my_player).toBe("A1");
    });

    it("기본 partner는 A2", () => {
      expect(useGameStore.getState().config.partner).toBe("A2");
    });
  });

  describe("setConfig", () => {
    it("부분 업데이트 적용", () => {
      useGameStore.getState().setConfig({ rule_mode: "bwf_21" });
      expect(useGameStore.getState().config.rule_mode).toBe("bwf_21");
    });

    it("다른 필드는 유지", () => {
      useGameStore.getState().setConfig({ rule_mode: "bwf_21" });
      expect(useGameStore.getState().config.my_player).toBe("A1");
    });

    it("my_player 변경", () => {
      useGameStore.getState().setConfig({ my_player: "A2" });
      expect(useGameStore.getState().config.my_player).toBe("A2");
    });
  });

  describe("setVideoFile", () => {
    it("파일 설정 시 videoFileName도 업데이트", () => {
      const file = new File(["content"], "game.mp4", { type: "video/mp4" });
      useGameStore.getState().setVideoFile(file);
      expect(useGameStore.getState().videoFileName).toBe("game.mp4");
    });

    it("null 설정 시 videoFileName은 빈 문자열", () => {
      const file = new File(["content"], "game.mp4", { type: "video/mp4" });
      useGameStore.getState().setVideoFile(file);
      useGameStore.getState().setVideoFile(null);
      expect(useGameStore.getState().videoFileName).toBe("");
    });

    it("파일 객체 저장", () => {
      const file = new File(["content"], "game.mp4", { type: "video/mp4" });
      useGameStore.getState().setVideoFile(file);
      expect(useGameStore.getState().videoFile).toBe(file);
    });
  });

  describe("reset", () => {
    it("모든 상태 초기화", () => {
      useGameStore.getState().setConfig({ rule_mode: "bwf_21" });
      useGameStore.getState().setVideoFile(new File(["x"], "test.mp4"));
      useGameStore.getState().reset();

      const state = useGameStore.getState();
      expect(state.config.rule_mode).toBe("amateur");
      expect(state.videoFile).toBeNull();
      expect(state.videoFileName).toBe("");
    });
  });
});
