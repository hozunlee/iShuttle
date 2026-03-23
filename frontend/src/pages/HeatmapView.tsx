import { useJobStore } from "../store/jobStore";
import Heatmap from "../components/Heatmap";

const FORMATION_LABEL: Record<string, string> = {
  front_back: "전후 공격",
  side_by_side: "좌우 수비",
  transition: "과도기",
};

export default function HeatmapView() {
  const { result } = useJobStore();
  if (!result) return null;

  const totalRallies = result.rallies.length;

  const formationCounts = result.rallies.reduce(
    (acc, r) => {
      const f = r.formation.dominant;
      acc[f] = (acc[f] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="space-y-6">
      <Heatmap heatmapUrl={result.heatmap_url} gameId={result.game_id} />

      {/* 포메이션 통계 */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">포메이션 분포</h3>
        {totalRallies === 0 ? (
          <p className="text-center text-gray-500 py-4">랠리 데이터가 없습니다</p>
        ) : (
          <div className="space-y-3">
            {Object.entries(formationCounts).map(([key, count]) => {
              const pct = Math.round((count / totalRallies) * 100);
              return (
                <div key={key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-300">{FORMATION_LABEL[key] || key}</span>
                    <span className="text-gray-400">
                      {count}랠리 ({pct}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="h-full bg-brand-500 rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
