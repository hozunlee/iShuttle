import type { AIReport, PoseSummary } from "../types/api";

interface Props {
  report: AIReport;
  poseSummary: PoseSummary;
  score: { us: number; them: number };
}

const CONFIDENCE_COLOR: Record<string, string> = {
  high: "text-green-400",
  medium: "text-yellow-400",
  low: "text-red-400",
};

export default function ReportCard({ report, poseSummary, score }: Props) {
  return (
    <div className="space-y-6">
      {/* 최종 스코어 */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 text-center">
        <p className="text-gray-400 text-sm mb-2">최종 스코어</p>
        <div className="flex items-center justify-center gap-6">
          <div>
            <p className="text-5xl font-bold text-white">{score.us}</p>
            <p className="text-sm text-brand-400 mt-1">우리팀</p>
          </div>
          <span className="text-3xl text-gray-500">:</span>
          <div>
            <p className="text-5xl font-bold text-white">{score.them}</p>
            <p className="text-sm text-gray-400 mt-1">상대팀</p>
          </div>
        </div>
        <p className="mt-3 text-lg font-semibold">
          {score.us > score.them ? "🏆 승리" : "💪 패배"}
        </p>
      </div>

      {/* AI 총평 */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
          AI 총평
        </h3>
        <p className="text-gray-200 leading-relaxed">{report.summary}</p>
      </div>

      {/* 잘한 점 */}
      <div className="bg-green-900/20 rounded-xl border border-green-500/20 p-6">
        <h3 className="text-sm font-semibold text-green-400 uppercase tracking-wider mb-3">
          👍 잘한 점
        </h3>
        <p className="text-gray-200 leading-relaxed">{report.pros}</p>
      </div>

      {/* 개선할 점 */}
      <div className="bg-orange-900/20 rounded-xl border border-orange-500/20 p-6">
        <h3 className="text-sm font-semibold text-orange-400 uppercase tracking-wider mb-3">
          📈 개선할 점
        </h3>
        <ul className="space-y-2">
          {report.cons.map((con, i) => (
            <li key={i} className="flex items-start gap-2 text-gray-200">
              <span className="text-orange-400 mt-0.5">•</span>
              <span>{con}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 집중 포인트 */}
      <div className="bg-brand-900/20 rounded-xl border border-brand-500/20 p-6">
        <h3 className="text-sm font-semibold text-brand-400 uppercase tracking-wider mb-3">
          🎯 다음 게임 집중 포인트
        </h3>
        <p className="text-gray-200 leading-relaxed">{report.focus}</p>
      </div>

      {/* 자세 수치 */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
            자세 분석
          </h3>
          <span className={`text-xs font-semibold ${CONFIDENCE_COLOR[poseSummary.confidence]}`}>
            신뢰도: {poseSummary.confidence}
          </span>
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-3xl font-bold text-white">{poseSummary.shoulder_rotation_avg}°</p>
            <p className="text-xs text-gray-400 mt-1">어깨 회전각</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-white">{poseSummary.spine_tilt_avg}°</p>
            <p className="text-xs text-gray-400 mt-1">척추 기울기</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-white">{poseSummary.knee_bend_avg}°</p>
            <p className="text-xs text-gray-400 mt-1">무릎 굽힘각</p>
          </div>
        </div>
      </div>
    </div>
  );
}
