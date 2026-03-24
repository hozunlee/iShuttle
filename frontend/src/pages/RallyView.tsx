import { useState } from "react";
import { useJobStore } from "../store/jobStore";
import { useBookmarkStore } from "../store/bookmarkStore";
import RallyCard from "../components/RallyCard";
import type { Rally } from "../types/api";

type Filter = "all" | "us" | "them" | "bookmarked";

export default function RallyView() {
  const { result } = useJobStore();
  const { isBookmarked, count: bookmarkCount } = useBookmarkStore();
  const [filter, setFilter] = useState<Filter>("all");
  const [sortByScore, setSortByScore] = useState(false);

  if (!result) return null;

  const scoreRally = (r: Rally) => r.strokes * 2 + (r.result === "us" ? 10 : 0);

  let rallies = result.rallies.filter((r) => {
    if (filter === "bookmarked") return isBookmarked(r.id);
    return filter === "all" || r.result === filter;
  });
  if (sortByScore) {
    rallies = [...rallies].sort((a, b) => scoreRally(b) - scoreRally(a));
  }

  return (
    <div>
      {/* 필터 & 정렬 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-2">
          {(["all", "us", "them", "bookmarked"] as Filter[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition-colors
                ${filter === f
                  ? f === "bookmarked" ? "bg-yellow-600 text-white" : "bg-brand-600 text-white"
                  : "bg-gray-700 text-gray-300 hover:bg-gray-600"}`}
            >
              {f === "all" ? "전체" : f === "us" ? "득점" : f === "them" ? "실점" : `★ 저장됨 (${bookmarkCount()})`}
            </button>
          ))}
        </div>
        <button
          onClick={() => setSortByScore(!sortByScore)}
          className={`text-sm px-3 py-1.5 rounded-lg transition-colors
            ${sortByScore ? "bg-yellow-600/30 text-yellow-400 border border-yellow-500/30" : "bg-gray-700 text-gray-300 hover:bg-gray-600"}`}
        >
          {sortByScore ? "★ 점수순" : "시간순"}
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {rallies.map((rally) => (
          <RallyCard key={rally.id} rally={rally} />
        ))}
      </div>

      {rallies.length === 0 && (
        <div className="text-center text-gray-500 py-12">해당 조건의 랠리가 없습니다</div>
      )}
    </div>
  );
}
