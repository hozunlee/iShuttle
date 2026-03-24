import { useJobStore } from "../store/jobStore";
import { useBookmarkStore } from "../store/bookmarkStore";

export default function PracticeView() {
  const { result } = useJobStore();
  const { isBookmarked, toggle } = useBookmarkStore();

  if (!result) return null;

  const bookmarked = result.rallies.filter((r) => isBookmarked(r.id));

  if (bookmarked.length === 0) {
    return (
      <div className="text-center py-16 space-y-3">
        <p className="text-4xl">☆</p>
        <p className="text-gray-400">저장된 랠리가 없습니다</p>
        <p className="text-gray-500 text-sm">랠리 클립 탭에서 ★ 를 눌러 연습할 랠리를 저장하세요</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-gray-400 text-sm">{bookmarked.length}개 저장됨 — 루프 재생 중</p>
      </div>

      <div className="space-y-6">
        {bookmarked.map((rally) => {
          const duration = (rally.timestamp.end_sec - rally.timestamp.start_sec).toFixed(1);
          return (
            <div
              key={rally.id}
              className="bg-gray-800 rounded-xl border border-yellow-500/30 overflow-hidden"
            >
              {rally.clip_url ? (
                <div className="bg-black aspect-video">
                  <video
                    src={rally.clip_url}
                    controls
                    loop
                    autoPlay
                    muted
                    className="w-full h-full object-contain"
                  />
                </div>
              ) : (
                <div className="aspect-video bg-gray-900 flex items-center justify-center text-gray-500">
                  클립 없음
                </div>
              )}

              <div className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <span className="text-gray-400 text-sm font-mono">
                    #{String(rally.id).padStart(3, "0")}
                  </span>
                  <span className="text-gray-300 text-sm">
                    {rally.strokes}타 · {duration}s
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${
                    rally.result === "us"
                      ? "bg-green-500/20 text-green-400 border-green-500/30"
                      : rally.result === "them"
                      ? "bg-red-500/20 text-red-400 border-red-500/30"
                      : "bg-gray-500/20 text-gray-400 border-gray-500/30"
                  }`}>
                    {rally.result === "us" ? "득점" : rally.result === "them" ? "실점" : "-"}
                  </span>
                </div>
                <button
                  onClick={() => toggle(rally.id)}
                  className="text-yellow-400 hover:text-gray-500 text-xl transition-colors"
                  title="연습 목록에서 제거"
                >
                  ★
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
