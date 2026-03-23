import { api } from "./client";
import type { RallyReport, JobStatus } from "../types/api";

/**
 * 분석 진행 상태 폴링
 */
export async function getStatus(jobId: string): Promise<JobStatus> {
  const res = await api.get<JobStatus>(`/api/status/${jobId}`);
  return res.data;
}

/**
 * 분석 결과 RallyReport 조회
 */
export async function getResults(jobId: string): Promise<RallyReport> {
  const res = await api.get<RallyReport>(`/api/results/${jobId}`);
  return res.data;
}
