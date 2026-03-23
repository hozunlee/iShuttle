import { useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useJobStore } from "../store/jobStore";
import { subscribeProgress } from "../api/client";
import { getStatus, getResults } from "../api/results";
import ProgressBar from "../components/ProgressBar";
import { mockProgressSteps, mockReport } from "../api/mock";

const USE_MOCK = import.meta.env.DEV && import.meta.env.VITE_USE_MOCK === "true";

export default function Analyzing() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { progress, step, status, updateProgress, setDone, setError } = useJobStore();
  const cleanupRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!jobId) return;

    if (USE_MOCK) {
      // Mock: 500ms 간격으로 진행률 시뮬레이션
      let idx = 0;
      const interval = setInterval(() => {
        if (idx >= mockProgressSteps.length) {
          clearInterval(interval);
          setDone(mockReport);
          navigate(`/results/${jobId}`);
          return;
        }
        const s = mockProgressSteps[idx];
        updateProgress(s.progress, s.step);
        if (s.status === "done") {
          clearInterval(interval);
          setDone(mockReport);
          navigate(`/results/${jobId}`);
        }
        idx++;
      }, 600);
      return () => clearInterval(interval);
    }

    let finished = false;
    let pollIntervalId: ReturnType<typeof setInterval> | null = null;

    const stopPolling = () => {
      if (pollIntervalId !== null) {
        clearInterval(pollIntervalId);
        pollIntervalId = null;
      }
    };

    const handleDone = async () => {
      if (finished) return;
      finished = true;
      stopPolling();
      try {
        const result = await getResults(jobId);
        setDone(result);
        navigate(`/results/${jobId}`);
      } catch (e) {
        setError("결과를 불러오지 못했습니다");
      }
    };

    // HTTP 폴링 (3초 간격) — WS 실패 시 fallback
    pollIntervalId = setInterval(async () => {
      if (finished) { stopPolling(); return; }
      try {
        const s = await getStatus(jobId);
        updateProgress(s.progress, s.step);
        if (s.status === "done" || s.progress >= 100) {
          stopPolling();
          await handleDone();
        } else if (s.status === "error") {
          stopPolling();
          finished = true;
          setError(s.step ?? "파이프라인 오류가 발생했습니다");
        }
      } catch {
        // 폴링 실패는 무시 (WS가 살아있으면 WS로 처리)
      }
    }, 3000);

    // WebSocket (더 빠른 실시간 업데이트)
    const cleanup = subscribeProgress(
      jobId,
      async (jobStatus) => {
        updateProgress(jobStatus.progress, jobStatus.step);

        if (jobStatus.status === "done" || jobStatus.progress >= 100) {
          stopPolling();
          await handleDone();
        } else if (jobStatus.status === "error") {
          stopPolling();
          finished = true;
          setError(jobStatus.step ?? "파이프라인 오류가 발생했습니다");
        }
      },
      () => {
        // WS 연결 실패 시 폴링이 계속 동작하므로 에러 표시 안 함
        console.warn("[WS] 연결 실패, HTTP 폴링으로 진행");
      }
    );

    cleanupRef.current = cleanup;
    return () => {
      stopPolling();
      cleanupRef.current?.();
    };
  }, [jobId]);

  const STEPS = [
    { label: "코트 감지", threshold: 10 },
    { label: "선수 추적", threshold: 30 },
    { label: "랠리 분리", threshold: 55 },
    { label: "클립 편집", threshold: 70 },
    { label: "자세 분석", threshold: 85 },
    { label: "AI 리포트", threshold: 100 },
  ];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg space-y-10">
        <div className="text-center">
          <h1 className="text-3xl font-black">
            <span className="text-brand-400">i</span>
            <span className="text-white">Shuttle</span>
          </h1>
          <p className="text-gray-400 mt-2">배드민턴 영상 분석 중...</p>
        </div>

        {/* 진행률 */}
        <ProgressBar progress={progress} step={step} />

        {/* 단계 표시 */}
        <div className="grid grid-cols-3 gap-3">
          {STEPS.map((s) => {
            const done = progress >= s.threshold;
            const active = !done && progress >= s.threshold - 25;
            return (
              <div
                key={s.label}
                className={`rounded-lg p-3 text-center text-sm transition-colors
                  ${done ? "bg-brand-600/20 border border-brand-500/40 text-brand-300" :
                    active ? "bg-gray-700 border border-gray-600 text-gray-200 animate-pulse" :
                    "bg-gray-800 border border-gray-700 text-gray-500"}`}
              >
                {done ? "✓ " : ""}{s.label}
              </div>
            );
          })}
        </div>

        {status === "error" && (
          <div className="bg-red-900/30 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm text-center">
            오류가 발생했습니다. 새로고침 후 다시 시도해주세요.
          </div>
        )}

        <p className="text-center text-xs text-gray-500">
          20분 영상 기준 약 3~5분 소요됩니다
        </p>
      </div>
    </div>
  );
}
