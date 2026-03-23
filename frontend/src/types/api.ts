// CONTEXT.md의 RallyReport JSON 스키마와 1:1 대응
// 주의: Spec.md의 타입과 다른 부분은 CONTEXT.md 기준으로 수정됨

export interface GameRule {
  mode: "amateur" | "bwf_21";
  win_score: number;
  deuce_trigger: number;
  deuce_cap: number;
  court_change_at: number;
}

export interface DetectionGap {
  start_frame: number;
  end_frame: number;
  interpolated: boolean;
}

export interface Rally {
  id: number;
  timestamp: { start_sec: number; end_sec: number };
  strokes: number;
  result: "us" | "them" | "neutral";
  score_at_end: { us: number; them: number };
  phase: "phase1" | "phase2" | "phase3" | "deuce";
  formation: {
    dominant: "front_back" | "side_by_side" | "transition";
    transitions: number;
  };
  clip_url: string;
  short_url: string;
  detection_gaps: DetectionGap[];
}

export interface PoseSummary {
  shoulder_rotation_avg: number;
  spine_tilt_avg: number;
  knee_bend_avg: number;
  confidence: "high" | "medium" | "low";
}

export interface AIReport {
  summary: string;
  pros: string;
  cons: string[];
  focus: string;
}

export interface RallyReport {
  game_id: string;
  rule: GameRule;
  score: { us: number; them: number };
  rallies: Rally[];
  heatmap_url: string;
  pose_summary: PoseSummary;
  ai_report: AIReport;
}

export interface JobStatus {
  progress: number; // 0~100
  step: string;
  status?: "processing" | "done" | "error";
}

export interface AnalyzeResponse {
  job_id: string;
  status: "processing";
}

export interface FeedbackResponse {
  summary: string;
  pros: string;
  cons: string[];
  focus: string;
}

export interface GameConfig {
  my_player: "A1" | "A2";
  partner: "A1" | "A2";
  rule_mode: "amateur" | "bwf_21";
}
