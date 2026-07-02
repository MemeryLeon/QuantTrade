import { expect, test, type Page } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    if (!window.sessionStorage.getItem("quanttrade.e2e.storageCleared")) {
      window.localStorage.clear();
      window.sessionStorage.setItem("quanttrade.e2e.storageCleared", "true");
    }
  });
});

test("loads market data and switches instrument", async ({ page }) => {
  await mockHealthyMarket(page);
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /平安银行/ })).toBeVisible();
  await expect(page.getByText("K 线与成交量")).toBeVisible();
  await expect(page.getByText("SMA20")).toBeVisible();

  await page.getByRole("button", { name: "浦发银行 600000" }).click();

  await expect(page.getByRole("heading", { name: /浦发银行/ })).toBeVisible();
});

test("switches resolution, adjustment and indicator parameters", async ({ page }) => {
  const indicatorUrls: string[] = [];
  const barUrls: string[] = [];
  await mockHealthyMarket(page, {
    onBarsRequest: (url) => barUrls.push(url),
    onIndicatorsRequest: (url) => indicatorUrls.push(url),
  });
  await page.goto("/");

  await page.getByRole("button", { name: "周线" }).click();
  await page.getByLabel("复权").selectOption("hfq");
  await page.getByLabel("指标管理").getByLabel("MACD 快线").fill("5");
  await page.getByLabel("指标管理").getByText("ADX").click();

  await expect.poll(() => barUrls.some((url) => url.includes("resolution=weekly"))).toBeTruthy();
  await expect.poll(() => barUrls.some((url) => url.includes("adjustment=hfq"))).toBeTruthy();
  await expect
    .poll(() => indicatorUrls.some((url) => url.includes("macd_fast_period=5")))
    .toBeTruthy();
});

test("shows global warning when data source degrades", async ({ page }) => {
  await mockHealthyMarket(page, {
    healthStatus: "degraded",
    delayed: true,
  });

  await page.goto("/");

  await expect(page.getByRole("alert", { name: "全局数据警告" })).toContainText("degraded");
  await expect(page.getByText("STALE_CACHE, PROVIDER_DEGRADED")).toBeVisible();
});

test("shows market request errors", async ({ page }) => {
  await page.route("**/market/data-sources/akshare/health", async (route) => {
    await route.fulfill({ json: healthPayload("healthy") });
  });
  await page.route("**/market/instruments/search**", async (route) => {
    await route.fulfill({ json: searchPayload() });
  });
  await page.route("**/market/bars**", async (route) => {
    await route.fulfill({
      status: 500,
      json: { code: "DATA_SOURCE_UNAVAILABLE", message: "akshare unavailable" },
    });
  });
  await page.route("**/market/indicators**", async (route) => {
    await route.fulfill({ json: indicatorsPayload(false) });
  });

  await page.goto("/");

  await expect(page.getByText(/DATA_SOURCE_UNAVAILABLE|请求失败/)).toBeVisible();
});

test("persists watchlist and rejects invalid import json", async ({ page }) => {
  await mockHealthyMarket(page);
  await page.goto("/");

  await page.getByRole("button", { name: "加入自选" }).click();
  await expect(
    page.getByLabel("自选标的").getByRole("button", { name: "平安银行 000001" }),
  ).toBeVisible();

  await page.reload();
  await expect(
    page.getByLabel("自选标的").getByRole("button", { name: "平安银行 000001" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "导出 JSON" }).click();
  await expect(page.getByLabel("导出内容")).toHaveValue(/"version": 1/);

  await page.getByLabel("导入 JSON").fill("{bad");
  await page.getByRole("button", { name: "导入" }).click();

  await expect(page.getByText("导入 JSON 格式不正确")).toBeVisible();
});

async function mockHealthyMarket(
  page: Page,
  options: {
    healthStatus?: "healthy" | "degraded";
    delayed?: boolean;
    onBarsRequest?: (url: string) => void;
    onIndicatorsRequest?: (url: string) => void;
  } = {},
) {
  const healthStatus = options.healthStatus ?? "healthy";
  const delayed = options.delayed ?? false;
  await page.route("**/market/data-sources/akshare/health", async (route) => {
    await route.fulfill({ json: healthPayload(healthStatus) });
  });
  await page.route("**/market/instruments/search**", async (route) => {
    await route.fulfill({ json: searchPayload() });
  });
  await page.route("**/market/bars**", async (route) => {
    options.onBarsRequest?.(route.request().url());
    await route.fulfill({ json: barsPayload(delayed) });
  });
  await page.route("**/market/indicators**", async (route) => {
    options.onIndicatorsRequest?.(route.request().url());
    await route.fulfill({ json: indicatorsPayload(delayed) });
  });
}

function healthPayload(status: "healthy" | "degraded") {
  return {
    provider: "akshare",
    status,
    checked_at: "2026-07-02T08:00:00Z",
    consecutive_failures: status === "healthy" ? 0 : 2,
    last_success_at: "2026-07-02T07:30:00Z",
    last_error_code: status === "healthy" ? null : "TIMEOUT",
    stale_cache_available: status !== "healthy",
    stale_age_seconds: status === "healthy" ? null : 1800,
  };
}

function searchPayload() {
  return {
    instruments: [
      {
        instrument_id: "CN_A:000001",
        symbol: "000001",
        name: "平安银行",
        market: "CN_A",
        exchange_timezone: "Asia/Shanghai",
      },
      {
        instrument_id: "CN_A:600000",
        symbol: "600000",
        name: "浦发银行",
        market: "CN_A",
        exchange_timezone: "Asia/Shanghai",
      },
    ],
  };
}

function barsPayload(delayed: boolean) {
  return {
    instrument_id: "CN_A:000001",
    provider: "akshare",
    market: "CN_A",
    currency: "CNY",
    resolution: "daily",
    adjustment: "qfq",
    timezone: "Asia/Shanghai",
    bars: Array.from({ length: 30 }, (_, index) => {
      const close = 10 + index * 0.15;
      return {
        observed_at: `2026-06-${String(index + 1).padStart(2, "0")}T07:00:00Z`,
        open_price: (close - 0.06).toFixed(2),
        high_price: (close + 0.18).toFixed(2),
        low_price: (close - 0.22).toFixed(2),
        close_price: close.toFixed(2),
        volume: 1000 + index * 20,
        quality_flags: [],
      };
    }),
    as_of: "2026-07-02T07:00:00Z",
    is_delayed: delayed,
    stale_age_seconds: delayed ? 1800 : null,
    quality_flags: delayed ? ["STALE_CACHE", "PROVIDER_DEGRADED"] : [],
  };
}

function indicatorsPayload(delayed: boolean) {
  return {
    instrument_id: "CN_A:000001",
    provider: "akshare",
    market: "CN_A",
    currency: "CNY",
    resolution: "daily",
    adjustment: "qfq",
    timezone: "Asia/Shanghai",
    parameters: {
      sma_period: 20,
      ema_period: 20,
      macd_fast_period: 12,
      macd_slow_period: 26,
      macd_signal_period: 9,
      rsi_period: 14,
      bollinger_period: 20,
      bollinger_multiplier: 2,
      adx_period: 14,
    },
    points: Array.from({ length: 30 }, (_, index) => {
      const value = index < 19 ? null : (10 + index * 0.12).toFixed(4);
      return {
        observed_at: `2026-06-${String(index + 1).padStart(2, "0")}T07:00:00Z`,
        sma: value,
        ema: value,
        macd: index < 25 ? null : "0.1200",
        macd_signal: index < 25 ? null : "0.1000",
        macd_histogram: index < 25 ? null : "0.0200",
        rsi: index < 14 ? null : "61.5000",
        bollinger_middle: value,
        bollinger_upper: value,
        bollinger_lower: value,
        adx: index < 27 ? null : "24.1000",
      };
    }),
    as_of: "2026-07-02T07:00:00Z",
    is_delayed: delayed,
    stale_age_seconds: delayed ? 1800 : null,
    quality_flags: delayed ? ["STALE_CACHE", "PROVIDER_DEGRADED"] : [],
  };
}
