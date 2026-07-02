import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { submitMockBacktest } from "../services/backtests";
import type { MockBacktestRequest } from "../services/backtests";
import { useBacktestStore } from "../stores/backtestStore";

const defaultRequest: MockBacktestRequest = {
  strategy_version_id: "strategy-version-1",
  instruments: ["000001.SZ"],
  start_date: "2026-01-01",
  end_date: "2026-01-31",
  resolution: "daily",
  adjustment: "qfq",
  initial_capital: "100000.00",
  base_currency: "CNY",
  benchmark: "000300.SH",
  parameters: [
    { name: "fast", value: 5 },
    { name: "slow", value: 20 },
  ],
  commission_model: "mock",
  slippage_model: "mock",
  data_snapshot_id: "snapshot-1",
};

export function MockBacktestPage() {
  const navigate = useNavigate();
  const setCurrentJobId = useBacktestStore((state) => state.setCurrentJobId);
  const mutation = useMutation({
    mutationFn: () => submitMockBacktest(defaultRequest),
    onSuccess: (submission) => {
      if (submission.job_id) {
        setCurrentJobId(submission.job_id);
        navigate(`/mock-backtests/${submission.job_id}`);
      }
    },
  });

  return (
    <main className="workspace">
      <section className="toolbar" aria-labelledby="mock-title">
        <div>
          <p className="eyebrow">B 阶段 Mock 引擎</p>
          <h2 id="mock-title">提交回测</h2>
        </div>
        <button type="button" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          {mutation.isPending ? "提交中" : "提交 Mock 回测"}
        </button>
      </section>

      <section className="details-grid" aria-label="回测请求">
        <div>
          <span>策略版本</span>
          <strong>{defaultRequest.strategy_version_id}</strong>
        </div>
        <div>
          <span>标的</span>
          <strong>{defaultRequest.instruments.join(", ")}</strong>
        </div>
        <div>
          <span>区间</span>
          <strong>
            {defaultRequest.start_date} 至 {defaultRequest.end_date}
          </strong>
        </div>
        <div>
          <span>初始资金</span>
          <strong>{defaultRequest.initial_capital} CNY</strong>
        </div>
      </section>

      {mutation.error ? <p className="error-text">{mutation.error.message}</p> : null}
    </main>
  );
}
