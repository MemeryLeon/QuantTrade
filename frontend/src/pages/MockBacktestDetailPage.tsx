import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import {
  cancelJob,
  getJobLogs,
  getJobStatus,
  getMockBacktestResult,
} from "../services/backtests";

const terminalStates = new Set(["succeeded", "failed", "cancelled", "timed_out"]);

export function MockBacktestDetailPage() {
  const { jobId } = useParams();
  const queryClient = useQueryClient();
  const safeJobId = jobId ?? "";
  const statusQuery = useQuery({
    queryKey: ["job-status", safeJobId],
    queryFn: () => getJobStatus(safeJobId),
    enabled: safeJobId.length > 0,
    refetchInterval: (query) => {
      const state = query.state.data?.state;
      return state && !terminalStates.has(state) ? 1000 : false;
    },
  });
  const logsQuery = useQuery({
    queryKey: ["job-logs", safeJobId],
    queryFn: () => getJobLogs(safeJobId),
    enabled: safeJobId.length > 0,
  });
  const resultQuery = useQuery({
    queryKey: ["mock-result", safeJobId],
    queryFn: () => getMockBacktestResult(safeJobId),
    enabled: statusQuery.data?.state === "succeeded",
  });
  const cancelMutation = useMutation({
    mutationFn: () => cancelJob(safeJobId),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["job-status", safeJobId] });
      void queryClient.invalidateQueries({ queryKey: ["job-logs", safeJobId] });
    },
  });

  const status = statusQuery.data;
  const canCancel = Boolean(status && !terminalStates.has(status.state));

  return (
    <main className="workspace">
      <section className="toolbar" aria-labelledby="job-title">
        <div>
          <p className="eyebrow">任务</p>
          <h2 id="job-title">{safeJobId || "未知任务"}</h2>
        </div>
        <div className="actions">
          <Link className="secondary-button" to="/mock-backtests">
            新建回测
          </Link>
          <button
            type="button"
            onClick={() => cancelMutation.mutate()}
            disabled={!canCancel || cancelMutation.isPending}
          >
            取消
          </button>
        </div>
      </section>

      {status ? (
        <section className="status-strip" aria-label="任务状态">
          <div>
            <span>状态</span>
            <strong>{status.state}</strong>
          </div>
          <div>
            <span>进度</span>
            <strong>{status.progress_percent}%</strong>
          </div>
          <div>
            <span>消息</span>
            <strong>{status.message ?? "-"}</strong>
          </div>
        </section>
      ) : null}

      {statusQuery.error ? <p className="error-text">{statusQuery.error.message}</p> : null}
      {cancelMutation.error ? <p className="error-text">{cancelMutation.error.message}</p> : null}

      {resultQuery.data ? (
        <section className="result-grid" aria-label="回测结果">
          <div>
            <span>总收益</span>
            <strong>{resultQuery.data.total_return_percent}%</strong>
          </div>
          <div>
            <span>最大回撤</span>
            <strong>{resultQuery.data.max_drawdown_percent}%</strong>
          </div>
          <div>
            <span>交易次数</span>
            <strong>{resultQuery.data.trade_count}</strong>
          </div>
          <div>
            <span>产物</span>
            <strong>{resultQuery.data.artifact_uri}</strong>
          </div>
        </section>
      ) : null}

      <section className="log-panel" aria-labelledby="log-title">
        <h3 id="log-title">日志</h3>
        <ol>
          {(logsQuery.data?.entries ?? []).map((entry) => (
            <li key={`${entry.created_at}-${entry.message}`}>
              <time dateTime={entry.created_at}>{new Date(entry.created_at).toLocaleString()}</time>
              <span>{entry.message}</span>
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
