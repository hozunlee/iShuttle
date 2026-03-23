import axios from "axios";
import type { JobStatus } from "../types/api";

export const api = axios.create({
  baseURL: "",
  timeout: 600000, // 10분 — 대용량 영상 업로드 대응
});

// 응답 인터셉터: 공통 에러 처리
api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error("[API] 오류:", err.response?.data ?? err.message);
    return Promise.reject(err);
  }
);

/**
 * WebSocket 진행률 구독
 * @returns cleanup 함수
 */
export function subscribeProgress(
  jobId: string,
  onUpdate: (s: JobStatus) => void,
  onError?: () => void
): () => void {
  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/progress/${jobId}`);

  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (!data.ping) {
        onUpdate(data as JobStatus);
      }
    } catch {
      console.warn("[WS] 파싱 오류:", e.data);
    }
  };

  ws.onerror = () => {
    console.error("[WS] 연결 오류");
    onError?.();
  };

  ws.onclose = () => {
    console.log("[WS] 연결 종료");
  };

  return () => ws.close();
}
