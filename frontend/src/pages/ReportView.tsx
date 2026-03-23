import { useJobStore } from "../store/jobStore";
import ReportCard from "../components/ReportCard";

export default function ReportView() {
  const { result } = useJobStore();
  if (!result) return null;

  return (
    <div>
      <ReportCard
        report={result.ai_report}
        poseSummary={result.pose_summary}
        score={result.score}
      />
    </div>
  );
}
