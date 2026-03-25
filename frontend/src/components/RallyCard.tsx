import { useState } from "react";
import type { Rally } from "../types/api";
import { useBookmarkStore } from "../store/bookmarkStore";
import { submitReport } from "../api/report";

interface Props {
  rally: Rally;
  jobId: string;
}

const REPORT_REASONS = [
  { value: "non_game", label: "게임 외 구간 (준비운동, 인터벌 등)" },
  { value: "boundary_error", label: "랠리 경계 오류 (시작/끝 시간 잘못됨)" },
  { value: "score_error", label: "득점 판정 오류 (득점/실점 반전)" },
  { value: "other", label: "기타" },
];

function ReportModal({
  rallyId,
  jobId,
  onClose,
  onDone,
}: {
  rallyId: number;
  jobId: string;
  onClose: () => void;
  onDone: () => void;
}) {
  const [reason, setReason] = useState("non_game");
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await submitReport({ rally_id: rallyId, job_id: jobId, reason, comment });
      onDone();
    } catch {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6 w-full max-w-sm mx-4 space-y-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-200">랠리 #{String(rallyId).padStart(3, "0")} 신고</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-xl">×</button>
        </div>

        <div className="space-y-2">
          {REPORT_REASONS.map((r) => (
            <label key={r.value} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="reason"
                value={r.value}
                checked={reason === r.value}
                onChange={() => setReason(r.value)}
                className="accent-brand-500"
              />
              <span className="text-sm text-gray-300">{r.label}</span>
            </label>
          ))}
        </div>

        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="추가 설명 (선택)"
          rows={2}
          className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-brand-500 resize-none"
        />

        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="w-full py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white text-sm font-semibold disabled:opacity-50"
        >
          {submitting ? "전송 중..." : "신고 제출"}
        </button>
      </div>
    </div>
  );
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

export default function RallyCard({ rally, jobId }: Props) {
  const [showShort, setShowShort] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [reported, setReported] = useState(false);
  const { isBookmarked, toggle } = useBookmarkStore();
  const bookmarked = isBookmarked(rally.id);
  const duration = (rally.timestamp.end_sec - rally.timestamp.start_sec).toFixed(1);

  return (
    <>
    {showReport && (
      <ReportModal
        rallyId={rally.id}
        jobId={jobId}
        onClose={() => setShowReport(false)}
        onDone={() => { setShowReport(false); setReported(true); }}
      />
    )}
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
          <div className="flex items-center gap-2">
            <span className={`text-xs px-2 py-0.5 rounded-full border ${RESULT_COLOR[rally.result]}`}>
              {RESULT_LABEL[rally.result]}
            </span>
            <button
              onClick={() => toggle(rally.id)}
              title={bookmarked ? "연습 목록에서 제거" : "연습 목록에 추가"}
              className={`text-xl leading-none transition-colors ${
                bookmarked ? "text-yellow-400" : "text-gray-600 hover:text-yellow-400"
              }`}
            >
              {bookmarked ? "★" : "☆"}
            </button>
            <button
              onClick={() => !reported && setShowReport(true)}
              title={reported ? "신고 완료" : "오류 신고"}
              className={`text-sm leading-none transition-colors ${
                reported ? "text-gray-600 cursor-default" : "text-gray-600 hover:text-red-400"
              }`}
            >
              {reported ? "🚩" : "⚑"}
            </button>
          </div>
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
    </>
  );
}
