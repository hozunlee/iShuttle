import { api } from "./client";
import type { FeedbackResponse } from "../types/api";

/**
 * 선택 랠리 기반 AI 피드백 요청
 */
export async function requestFeedback(
  gameId: string,
  rallyIds: number[]
): Promise<FeedbackResponse> {
  const res = await api.post<FeedbackResponse>("/api/feedback", {
    game_id: gameId,
    rally_ids: rallyIds,
  });
  return res.data;
}
