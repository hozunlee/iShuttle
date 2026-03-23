import { create } from "zustand";
import type { GameConfig } from "../types/api";

interface GameStore {
  config: GameConfig;
  videoFile: File | null;
  videoFileName: string;
  setConfig: (config: Partial<GameConfig>) => void;
  setVideoFile: (file: File | null) => void;
  reset: () => void;
}

const DEFAULT_CONFIG: GameConfig = {
  my_player: "A1",
  partner: "A2",
  rule_mode: "amateur",
};

export const useGameStore = create<GameStore>((set) => ({
  config: { ...DEFAULT_CONFIG },
  videoFile: null,
  videoFileName: "",

  setConfig: (partial) =>
    set((state) => ({ config: { ...state.config, ...partial } })),

  setVideoFile: (file) =>
    set({ videoFile: file, videoFileName: file?.name ?? "" }),

  reset: () => set({ config: { ...DEFAULT_CONFIG }, videoFile: null, videoFileName: "" }),
}));
