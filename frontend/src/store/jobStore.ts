import { create } from "zustand";
import type { RallyReport } from "../types/api";

type JobStatus = "idle" | "processing" | "done" | "error";

interface JobStore {
  jobId: string | null;
  progress: number;
  step: string;
  status: JobStatus;
  result: RallyReport | null;
  errorMessage: string;
  setJob: (jobId: string) => void;
  updateProgress: (progress: number, step: string) => void;
  setDone: (result: RallyReport) => void;
  setError: (message: string) => void;
  reset: () => void;
}

export const useJobStore = create<JobStore>((set) => ({
  jobId: null,
  progress: 0,
  step: "",
  status: "idle",
  result: null,
  errorMessage: "",

  setJob: (jobId) => set({ jobId, progress: 0, step: "대기 중...", status: "processing" }),

  updateProgress: (progress, step) => set({ progress, step }),

  setDone: (result) => set({ progress: 100, step: "완료", status: "done", result }),

  setError: (message) => set({ status: "error", errorMessage: message }),

  reset: () =>
    set({
      jobId: null,
      progress: 0,
      step: "",
      status: "idle",
      result: null,
      errorMessage: "",
    }),
}));
