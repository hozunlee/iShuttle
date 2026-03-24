import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Setup from "./pages/Setup";
import Analyzing from "./pages/Analyzing";
import Results from "./pages/Results";
import RallyView from "./pages/RallyView";
import HeatmapView from "./pages/HeatmapView";
import ReportView from "./pages/ReportView";
import PracticeView from "./pages/PracticeView";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Setup />} />
        <Route path="/analyzing/:jobId" element={<Analyzing />} />
        <Route path="/results/:jobId" element={<Results />}>
          <Route index element={<Navigate to="rallies" replace />} />
          <Route path="rallies" element={<RallyView />} />
          <Route path="heatmap" element={<HeatmapView />} />
          <Route path="report" element={<ReportView />} />
          <Route path="practice" element={<PracticeView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
