import { NavLink, Outlet, useParams, useNavigate } from "react-router-dom";
import { useJobStore } from "../store/jobStore";
import { useBookmarkStore } from "../store/bookmarkStore";
import { useEffect } from "react";
import { getResults } from "../api/results";
import { mockReport } from "../api/mock";

const USE_MOCK = import.meta.env.DEV && import.meta.env.VITE_USE_MOCK === "true";

const TAB_BASE = "px-5 py-3 text-sm font-semibold rounded-lg transition-colors";
const TAB_ACTIVE = "bg-brand-600 text-white";
const TAB_INACTIVE = "text-gray-400 hover:text-gray-200 hover:bg-gray-700";

export default function Results() {
  const { jobId } = useParams<{ jobId: string }>();
  const { result, setDone } = useJobStore();
  const { count: bookmarkCount } = useBookmarkStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (result) return;
    if (!jobId) return;

    // 페이지 직접 접근 시 결과 로드
    if (USE_MOCK) {
      setDone(mockReport);
      return;
    }

    getResults(jobId)
      .then(setDone)
      .catch(() => navigate("/"));
  }, [jobId]);

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        결과 로딩 중...
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* 헤더 */}
      <header className="border-b border-gray-800 px-4 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <button onClick={() => navigate("/")} className="text-gray-400 hover:text-white text-sm">
            ← 새 게임 분석
          </button>
          <h1 className="font-black text-lg">
            <span className="text-brand-400">i</span>
            <span className="text-white">Shuttle</span>
          </h1>
          <div className="text-right text-sm">
            <span className="text-white font-bold">{result.score.us}</span>
            <span className="text-gray-500 mx-1">:</span>
            <span className="text-gray-300">{result.score.them}</span>
          </div>
        </div>
      </header>

      {/* 탭 네비게이션 */}
      <nav className="border-b border-gray-800 px-4 py-2">
        <div className="max-w-3xl mx-auto flex gap-2">
          <NavLink
            to={`/results/${jobId}/rallies`}
            className={({ isActive }) => `${TAB_BASE} ${isActive ? TAB_ACTIVE : TAB_INACTIVE}`}
          >
            랠리 클립 ({result.rallies.length})
          </NavLink>
          <NavLink
            to={`/results/${jobId}/heatmap`}
            className={({ isActive }) => `${TAB_BASE} ${isActive ? TAB_ACTIVE : TAB_INACTIVE}`}
          >
            히트맵
          </NavLink>
          <NavLink
            to={`/results/${jobId}/report`}
            className={({ isActive }) => `${TAB_BASE} ${isActive ? TAB_ACTIVE : TAB_INACTIVE}`}
          >
            AI 리포트
          </NavLink>
          <NavLink
            to={`/results/${jobId}/practice`}
            className={({ isActive }) =>
              `${TAB_BASE} ${isActive ? "bg-yellow-600 text-white" : TAB_INACTIVE}`
            }
          >
            ★ 연습{bookmarkCount() > 0 ? ` (${bookmarkCount()})` : ""}
          </NavLink>
        </div>
      </nav>

      {/* 탭 콘텐츠 */}
      <main className="max-w-3xl mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
