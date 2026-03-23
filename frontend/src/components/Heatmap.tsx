interface Props {
  heatmapUrl: string;
  gameId: string;
}

export default function Heatmap({ heatmapUrl, gameId }: Props) {
  const fullUrl = heatmapUrl.startsWith("/static")
    ? `http://localhost:8000${heatmapUrl}`
    : heatmapUrl;

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
      <h3 className="text-lg font-semibold text-white mb-4">포지션 히트맵</h3>
      <div className="flex justify-center">
        <img
          src={fullUrl}
          alt={`게임 ${gameId} 히트맵`}
          className="max-w-full rounded-lg"
          onError={(e) => {
            (e.target as HTMLImageElement).src = "data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='600' viewBox='0 0 400 600'%3E%3Crect width='400' height='600' fill='%231f2937'/%3E%3Ctext x='50%25' y='50%25' font-size='16' fill='%236b7280' text-anchor='middle' dominant-baseline='middle'%3E히트맵 준비 중%3C/text%3E%3C/svg%3E";
          }}
        />
      </div>
      <p className="text-xs text-gray-400 text-center mt-3">
        코트 9구역 기준 선수 이동 빈도 시각화
      </p>
    </div>
  );
}
