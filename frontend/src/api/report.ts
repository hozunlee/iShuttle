import { api } from "./client";

export interface ReportPayload {
  rally_id: number;
  job_id: string;
  reason: string;
  comment?: string;
}

export async function submitReport(payload: ReportPayload): Promise<void> {
  await api.post("/api/report", payload);
}
