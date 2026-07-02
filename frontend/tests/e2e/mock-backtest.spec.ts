import { expect, test } from "@playwright/test";

test("submits a mock backtest and shows logs and result", async ({ page }) => {
  await page.route("**/backtests/mock", async (route) => {
    if (route.request().method() !== "POST") {
      await route.fallback();
      return;
    }
    await route.fulfill({
      json: {
        status: "accepted",
        job_id: "job-1",
        error_code: null,
        error_message: null,
        trace_id: "trace-e2e",
      },
    });
  });
  await page.route("**/jobs/job-1", async (route) => {
    await route.fulfill({
      json: {
        job_id: "job-1",
        state: "succeeded",
        progress_percent: 100,
        message: "mock backtest succeeded",
        updated_at: "2026-01-01T00:00:00Z",
        retry_count: 0,
        max_retries: 1,
        artifact_uri: "memory://mock-backtest/result",
      },
    });
  });
  await page.route("**/jobs/job-1/logs", async (route) => {
    await route.fulfill({
      json: {
        entries: [
          {
            job_id: "job-1",
            message: "mock backtest succeeded",
            created_at: "2026-01-01T00:00:00Z",
          },
        ],
      },
    });
  });
  await page.route("**/backtests/mock/job-1/result", async (route) => {
    await route.fulfill({
      json: {
        job_id: "job-1",
        state: "succeeded",
        artifact_uri: "memory://mock-backtest/result",
        total_return_percent: 3.42,
        max_drawdown_percent: 1.15,
        trade_count: 4,
      },
    });
  });

  await page.goto("/mock-backtests");
  await page.getByRole("button", { name: "提交 Mock 回测" }).click();

  await expect(page.getByRole("heading", { name: "job-1" })).toBeVisible();
  await expect(page.getByText("mock backtest succeeded").first()).toBeVisible();
  await expect(page.getByText("3.42%")).toBeVisible();
});
