import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useGameStore } from "../store/gameStore";
import { useJobStore } from "../store/jobStore";
import UploadZone from "../components/UploadZone";
import { startAnalysis } from "../api/analyze";
import { mockAnalyze } from "../api/mock";

const USE_MOCK = import.meta.env.DEV && import.meta.env.VITE_USE_MOCK === "true";

export default function Setup() {
  const navigate = useNavigate();
  const { config, videoFile, videoFileName, setConfig, setVideoFile } = useGameStore();
  const { setJob, setError } = useJobStore();
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const canSubmit = videoFile !== null;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setLoading(true);
    setErrorMsg("");

    try {
      let jobId: string;

      if (USE_MOCK) {
        const res = await mockAnalyze();
        jobId = res.job_id;
      } else {
        const res = await startAnalysis(videoFile!, config);
        jobId = res.job_id;
      }

      setJob(jobId);
      navigate(`/analyzing/${jobId}`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "분석 요청 실패";
      setErrorMsg(msg);
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
      {/* 헤더 */}
      <div className="text-center mb-10">
        <h1 className="text-4xl font-black tracking-tight">
          <span className="text-brand-400">i</span>
          <span className="text-white">Shuttle</span>
        </h1>
        <p className="text-gray-400 mt-2">눈으로 다시 보는 나의 배드민턴</p>
      </div>

      <div className="w-full max-w-lg space-y-6">
        {/* 영상 업로드 */}
        <div>
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            게임 영상
          </label>
          <UploadZone
            onFile={(file) => setVideoFile(file)}
            fileName={videoFileName}
          />
        </div>

        {/* 게임 설정 */}
        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6 space-y-4">
          <h2 className="font-semibold text-gray-200">게임 설정</h2>

          <div>
            <label className="block text-sm text-gray-400 mb-1.5">게임 모드</label>
            <select
              value={config.rule_mode}
              onChange={(e) => setConfig({ rule_mode: e.target.value as "amateur" | "bwf_21" })}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-gray-100 focus:outline-none focus:border-brand-500"
            >
              <option value="amateur">동호인 (25점, 듀스 24점)</option>
              <option value="bwf_21">BWF (21점, 듀스 20점)</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">내 포지션</label>
              <select
                value={config.my_player}
                onChange={(e) => setConfig({ my_player: e.target.value as "A1" | "A2" })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-gray-100 focus:outline-none focus:border-brand-500"
              >
                <option value="A1">A1 (왼쪽)</option>
                <option value="A2">A2 (오른쪽)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">파트너 포지션</label>
              <select
                value={config.partner}
                onChange={(e) => setConfig({ partner: e.target.value as "A1" | "A2" })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-gray-100 focus:outline-none focus:border-brand-500"
              >
                <option value="A1">A1 (왼쪽)</option>
                <option value="A2">A2 (오른쪽)</option>
              </select>
            </div>
          </div>
        </div>

        {errorMsg && (
          <div className="bg-red-900/30 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
            {errorMsg}
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={!canSubmit || loading}
          className="w-full py-4 rounded-2xl font-bold text-lg transition-all
            bg-brand-600 hover:bg-brand-500 text-white
            disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? "업로드 중..." : "분석 시작 🚀"}
        </button>

        <p className="text-center text-xs text-gray-500">
          로컬 PC에서 실행됩니다. 영상은 외부로 전송되지 않습니다.
        </p>
      </div>
    </div>
  );
}
