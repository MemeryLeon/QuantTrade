import { apiClient } from "../api/client";
import type { components } from "../api/generated/schema";

export type MockBacktestRequest = components["schemas"]["MockBacktestRequest"];
export type BacktestSubmission = components["schemas"]["BacktestSubmissionResponse"];
export type JobStatus = components["schemas"]["JobStatusResponse"];
export type JobLogs = components["schemas"]["JobLogsResponse"];
export type MockBacktestResult = components["schemas"]["MockBacktestResultResponse"];

type ApiErrorBody = {
  code?: string;
  message?: string;
};

function apiErrorMessage(error: unknown): string {
  const body = error as ApiErrorBody | undefined;
  if (body?.code && body?.message) {
    return `${body.code}: ${body.message}`;
  }
  return "请求失败";
}

export async function submitMockBacktest(body: MockBacktestRequest): Promise<BacktestSubmission> {
  const { data, error } = await apiClient.POST("/backtests/mock", { body });
  if (error || !data) {
    throw new Error(apiErrorMessage(error));
  }
  return data;
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const { data, error } = await apiClient.GET("/jobs/{job_id}", {
    params: { path: { job_id: jobId } },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error));
  }
  return data;
}

export async function getJobLogs(jobId: string): Promise<JobLogs> {
  const { data, error } = await apiClient.GET("/jobs/{job_id}/logs", {
    params: { path: { job_id: jobId } },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error));
  }
  return data;
}

export async function cancelJob(jobId: string): Promise<JobStatus> {
  const { data, error } = await apiClient.POST("/jobs/{job_id}/cancel", {
    params: { path: { job_id: jobId } },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error));
  }
  return data;
}

export async function getMockBacktestResult(jobId: string): Promise<MockBacktestResult> {
  const { data, error } = await apiClient.GET("/backtests/mock/{job_id}/result", {
    params: { path: { job_id: jobId } },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error));
  }
  return data;
}
