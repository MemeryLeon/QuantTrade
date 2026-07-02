import { Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { MarketPage } from "./pages/MarketPage";
import { MockBacktestDetailPage } from "./pages/MockBacktestDetailPage";
import { MockBacktestPage } from "./pages/MockBacktestPage";

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<MarketPage />} />
        <Route path="/mock-backtests" element={<MockBacktestPage />} />
        <Route path="/mock-backtests/:jobId" element={<MockBacktestDetailPage />} />
      </Route>
    </Routes>
  );
}
