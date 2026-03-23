import { useState } from "react";
import type { Rally } from "../types/api";

interface Props {
  rally: Rally;
}

const FORMATION_LABEL: Record<string, string> = {
  front_back: "전후 공격",
  side_by_side: "좌우 수비",
  transition: "과도기",
};

const RESULT_COLOR: Record<string, string> = {
  us: "bg-green-500/20 text-green-400 border-green-500/30",
  them: "bg-red-500/20 text-red-400 border-red-500/30",
  neutral: "bg-gray-500/20 text-gray-400 border-gray-500/30",
};

const RESULT_LABEL: Record<string, string> = {
  us: "득점",
  them: "실점",
  neutral: "-",
};

export default function RallyCard({ rally }: Props) {
  const [showShort, setShowShort] = useState(false);
  const duration = (rally.timestamp.end_sec - rally.timestamp.start_sec).toFixed(1);

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden hover:border-brand-500/50 transition-colors">
      {/* 비디오 플레이어 */}
      {rally.clip_url ? (
        <div className="relative bg-black aspect-video">
          <video
            src={showShort && rally.short_url ? rally.short_url : rally.clip_url}
            controls
            className="w-full h-full object-contain"
            preload="metadata"
          />
          {rally.short_url && (
            <button
              onClick={() => setShowShort(!showShort)}
              className="absolute top-2 right-2 text-xs bg-black/70 text-white px-2 py-1 rounded"
            >
              {showShort ? "원본" : "숏폼"}
            </button>
          )}
        </div>
      ) : (
        <div className="aspect-video bg-gray-900 flex items-center justify-center text-gray-500">
          클립 없음
        </div>
      )}

      {/* 메타 정보 */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-gray-400 text-sm font-mono">
            #{String(rally.id).padStart(3, "0")}
          </span>
          <span className={`text-xs px-2 py-0.5 rounded-full border ${RESULT_COLOR[rally.result]}`}>
            {RESULT_LABEL[rally.result]}
          </span>
        </div>

        <div className="grid grid-cols-3 gap-3 text-center">
          <div>
            <p className="text-2xl font-bold text-white">{rally.strokes}</p>
            <p className="text-xs text-gray-400">타수</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-white">{duration}s</p>
            <p className="text-xs text-gray-400">길이</p>
          </div>
          <div>
            <p className="text-sm font-semibold text-white">
              {FORMATION_LABEL[rally.formation.dominant]}
            </p>
            <p className="text-xs text-gray-400">포메이션</p>
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between text-sm">
          <span className="text-gray-400">
            {rally.score_at_end.us} : {rally.score_at_end.them}
          </span>
          <span className="text-gray-500 text-xs capitalize">{rally.phase}</span>
        </div>
      </div>
    </div>
  );
}
