// Mock API — BE 연동 전 FE 독립 개발용
// BE 연동 완료 시 이 파일의 import를 제거한다

import type {
  AnalyzeResponse,
  JobStatus,
  RallyReport,
  FeedbackResponse,
} from "../types/api";

export const mockAnalyze = async (): Promise<AnalyzeResponse> => ({
  job_id: "mock-001",
  status: "processing",
});

export const mockProgressSteps: JobStatus[] = [
  { progress: 5, step: "코트 라인 감지 중..." },
  { progress: 10, step: "코트 감지 완료" },
  { progress: 15, step: "선수 추적 중..." },
  { progress: 30, step: "선수 추적 완료" },
  { progress: 35, step: "셔틀콕 추적 & 랠리 분리 중..." },
  { progress: 55, step: "랠리 22개 감지 완료" },
  { progress: 60, step: "랠리 클립 편집 중..." },
  { progress: 70, step: "클립 편집 완료" },
  { progress: 75, step: "포메이션 분류 중..." },
  { progress: 80, step: "자세 분석 중..." },
  { progress: 85, step: "자세 분석 완료" },
  { progress: 90, step: "AI 리포트 생성 중..." },
  { progress: 100, step: "분석 완료!", status: "done" },
];

export const mockReport: RallyReport = {
  game_id: "mock-game-001",
  rule: {
    mode: "amateur",
    win_score: 25,
    deuce_trigger: 24,
    deuce_cap: 31,
    court_change_at: 13,
  },
  score: { us: 25, them: 18 },
  rallies: Array.from({ length: 22 }, (_, i) => ({
    id: i + 1,
    timestamp: {
      start_sec: 10 + i * 25,
      end_sec: 18 + i * 25 + Math.random() * 10,
    },
    strokes: 3 + Math.floor(Math.random() * 12),
    result: (i % 3 === 2 ? "them" : "us") as "us" | "them",
    score_at_end: {
      us: Math.min(25, Math.floor(i * 0.7) + 1),
      them: Math.min(18, Math.floor(i * 0.4)),
    },
    phase:
      i < 8
        ? "phase1"
        : i < 16
          ? "phase2"
          : ("phase3" as "phase1" | "phase2" | "phase3"),
    formation: {
      dominant: (
        ["front_back", "side_by_side", "transition"] as const
      )[i % 3],
      transitions: Math.floor(Math.random() * 4),
    },
    clip_url: `/static/clips/mock/rally_${String(i + 1).padStart(3, "0")}.mp4`,
    short_url: i < 3 ? `/static/shorts/mock/rally_${String(i + 1).padStart(3, "0")}_916.mp4` : "",
    detection_gaps: [],
  })),
  heatmap_url: "/static/heatmap/mock-game-001.png",
  pose_summary: {
    shoulder_rotation_avg: 48.2,
    spine_tilt_avg: 19.3,
    knee_bend_avg: 128.5,
    confidence: "high",
  },
  ai_report: {
    summary:
      "총 22개의 랠리에서 우리팀이 25점을 득점하며 승리했습니다. 전반적으로 전후 포메이션을 잘 활용한 공격적인 경기를 펼쳤습니다.",
    pros: "평균 7.3타의 랠리를 이어가며 안정적인 경기력을 보여줬습니다. 특히 전반부 front_back 포메이션 유지가 우수했습니다.",
    cons: [
      "포메이션 전환 구간에서 중앙 코트가 노출되는 빈도가 높았습니다. 파트너와의 간격 조율이 필요합니다.",
      "서브 후 첫 번째 리턴에서 실점 비율이 높습니다. 서브 방향 다양화를 연습하세요.",
    ],
    focus:
      "다음 게임에서는 전환 구간에 파트너와 즉각적인 포지션 콜을 하여 빈틈을 최소화해보세요.",
  },
};

export const mockFeedback: FeedbackResponse = {
  summary:
    "선택한 랠리들은 전반적으로 적극적인 스매시 공격 패턴을 보여줬습니다.",
  pros: "네트 전방 공격 시 정확한 타이밍을 유지했습니다.",
  cons: [
    "백핸드 클리어의 높이가 부족합니다.",
    "상대 스매시 대응 시 리시브 자세가 불안정합니다.",
  ],
  focus: "백핸드 그립 전환 속도를 높이는 연습을 집중적으로 하세요.",
};
