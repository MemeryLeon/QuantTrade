import { Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { MockBacktestDetailPage } from "./pages/MockBacktestDetailPage";
import { MockBacktestPage } from "./pages/MockBacktestPage";

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<MockBacktestPage />} />
        <Route path="/backtests/mock/:jobId" element={<MockBacktestDetailPage />} />
      </Route>
    </Routes>
  );
}
