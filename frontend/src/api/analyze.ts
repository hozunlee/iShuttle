import { api } from "./client";
import type { AnalyzeResponse, GameConfig } from "../types/api";

/**
 * 영상 파일 업로드 & 분석 시작
 */
export async function startAnalysis(
  videoFile: File,
  gameConfig: GameConfig
): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append("video_file", videoFile);
  formData.append("game_config", JSON.stringify(gameConfig));

  const res = await api.post<AnalyzeResponse>("/api/analyze", formData);
  return res.data;
}
