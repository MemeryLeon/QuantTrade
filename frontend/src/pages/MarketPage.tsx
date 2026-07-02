import { useQuery } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";

import { MarketChart, type IndicatorKey } from "../components/MarketChart";
import {
  getBars,
  getDataSourceHealth,
  getIndicators,
  getQuote,
  searchInstruments,
  type Adjustment,
  type Bars,
  type DataSourceHealth,
  type IndicatorParameters,
  type Indicators,
  type Instrument,
  type MarketResolution,
  type Quote,
} from "../services/market";
import { useWatchlistStore } from "../stores/watchlistStore";

type Bar = Bars["bars"][number];
type IndicatorPoint = Indicators["points"][number];

const defaultInstrument: Instrument = {
  instrument_id: "CN_A:000001",
  symbol: "000001",
  name: "平安银行",
  market: "CN_A",
  exchange_timezone: "Asia/Shanghai",
};

const adjustmentLabels: Record<Adjustment, string> = {
  none: "不复权",
  qfq: "前复权",
  hfq: "后复权",
};

const resolutionLabels: Record<MarketResolution, string> = {
  daily: "日线",
  weekly: "周线",
  monthly: "月线",
};

const defaultIndicatorParameters: IndicatorParameters = {
  sma_period: 20,
  ema_period: 20,
  macd_fast_period: 12,
  macd_slow_period: 26,
  macd_signal_period: 9,
  rsi_period: 14,
  bollinger_period: 20,
  bollinger_multiplier: "2",
  adx_period: 14,
};

const defaultVisibleIndicators: Record<IndicatorKey, boolean> = {
  sma: true,
  ema: true,
  bollinger: true,
  macd: true,
  rsi: false,
  adx: false,
};

const MARKET_PREFERENCES_KEY = "quanttrade.market.preferences.v1";
const SEARCH_STALE_MS = 60_000;
const MARKET_DATA_STALE_MS = 30_000;
const QUOTE_STALE_MS = 15_000;

type MarketPreferences = {
  resolution: MarketResolution;
  adjustment: Adjustment;
  indicatorParameters: IndicatorParameters;
  visibleIndicators: Record<IndicatorKey, boolean>;
  recentInstruments: Instrument[];
};

export function MarketPage() {
  const [initialPreferences] = useState(loadMarketPreferences);
  const [query, setQuery] = useState("平安");
  const [submittedQuery, setSubmittedQuery] = useState("平安");
  const [selectedInstrument, setSelectedInstrument] = useState<Instrument>(defaultInstrument);
  const [startDate, setStartDate] = useState(() => daysBeforeInputDate(180));
  const [endDate, setEndDate] = useState(() => inputDate(new Date()));
  const [resolution, setResolution] = useState<MarketResolution>(
    initialPreferences?.resolution ?? "daily",
  );
  const [adjustment, setAdjustment] = useState<Adjustment>(
    initialPreferences?.adjustment ?? "qfq",
  );
  const [indicatorParameters, setIndicatorParameters] = useState<IndicatorParameters>(
    initialPreferences?.indicatorParameters ?? defaultIndicatorParameters,
  );
  const [visibleIndicators, setVisibleIndicators] =
    useState<Record<IndicatorKey, boolean>>(
      initialPreferences?.visibleIndicators ?? defaultVisibleIndicators,
    );
  const [recentInstruments, setRecentInstruments] = useState<Instrument[]>(
    initialPreferences?.recentInstruments ?? [],
  );
  const [chartResetSignal, setChartResetSignal] = useState(0);
  const [chartFullscreen, setChartFullscreen] = useState(false);
  const [exportText, setExportText] = useState("");
  const [importText, setImportText] = useState("");
  const [importError, setImportError] = useState<string | null>(null);
  const watchlistItems = useWatchlistStore((state) => state.items);
  const addInstrument = useWatchlistStore((state) => state.addInstrument);
  const removeInstrument = useWatchlistStore((state) => state.removeInstrument);
  const exportWatchlist = useWatchlistStore((state) => state.exportJson);
  const importWatchlist = useWatchlistStore((state) => state.importJson);

  const healthQuery = useQuery({
    queryKey: ["market-health", "akshare"],
    queryFn: getDataSourceHealth,
    refetchInterval: 30_000,
  });
  const searchQuery = useQuery({
    queryKey: ["market-search", submittedQuery],
    queryFn: () => searchInstruments(submittedQuery),
    enabled: submittedQuery.trim().length > 0,
    staleTime: SEARCH_STALE_MS,
  });
  const quoteQuery = useQuery({
    queryKey: ["market-quote", selectedInstrument.instrument_id],
    queryFn: () => getQuote(selectedInstrument.instrument_id),
    refetchInterval: 30_000,
    staleTime: QUOTE_STALE_MS,
  });
  const barsQuery = useQuery({
    queryKey: ["market-bars", selectedInstrument.instrument_id, startDate, endDate, resolution, adjustment],
    queryFn: () =>
      getBars({
        instrumentId: selectedInstrument.instrument_id,
        start: toApiDateTime(startDate),
        end: toApiDateTime(endDate),
        resolution,
        adjustment,
      }),
    staleTime: MARKET_DATA_STALE_MS,
  });
  const indicatorsQuery = useQuery({
    queryKey: [
      "market-indicators",
      selectedInstrument.instrument_id,
      startDate,
      endDate,
      resolution,
      adjustment,
      indicatorParameters,
    ],
    queryFn: () =>
      getIndicators({
        instrumentId: selectedInstrument.instrument_id,
        start: toApiDateTime(startDate),
        end: toApiDateTime(endDate),
        resolution,
        adjustment,
        parameters: indicatorParameters,
      }),
    staleTime: MARKET_DATA_STALE_MS,
  });

  useEffect(() => {
    const handle = window.setTimeout(() => {
      setSubmittedQuery(query.trim());
    }, 350);
    return () => window.clearTimeout(handle);
  }, [query]);

  useEffect(() => {
    const first = searchQuery.data?.[0];
    if (first) {
      setSelectedInstrument(first);
    }
  }, [searchQuery.data]);

  useEffect(() => {
    setRecentInstruments((current) => rememberInstrument(current, selectedInstrument));
  }, [selectedInstrument]);

  useEffect(() => {
    saveMarketPreferences({
      resolution,
      adjustment,
      indicatorParameters,
      visibleIndicators,
      recentInstruments,
    });
  }, [adjustment, indicatorParameters, recentInstruments, resolution, visibleIndicators]);

  const indicatorPoints = indicatorsQuery.data?.points ?? [];
  const latestIndicator = indicatorPoints[indicatorPoints.length - 1];
  const warningText = warningMessage(healthQuery.data, barsQuery.data, indicatorsQuery.data);
  const quoteSummary = quoteDetails(quoteQuery.data, barsQuery.data);
  const selectedInWatchlist = watchlistItems.some(
    (item) => item.instrument_id === selectedInstrument.instrument_id,
  );

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmittedQuery(query.trim());
  }

  function addSelectedInstrument() {
    addInstrument(selectedInstrument);
    setExportText("");
  }

  function showExportJson() {
    setExportText(exportWatchlist());
  }

  function submitImport() {
    try {
      importWatchlist(importText);
      setImportError(null);
      setImportText("");
      setExportText("");
    } catch (error) {
      setImportError(error instanceof Error ? error.message : "导入失败");
    }
  }

  function updateIndicatorPeriod(key: keyof IndicatorParameters, value: string) {
    setIndicatorParameters((current) => ({
      ...current,
      [key]: key === "bollinger_multiplier" ? value : Number(value),
    }));
  }

  function toggleIndicator(key: IndicatorKey) {
    setVisibleIndicators((current) => ({ ...current, [key]: !current[key] }));
  }

  return (
    <main className="workspace market-workspace">
      {warningText ? (
        <section className="global-warning" role="alert" aria-label="全局数据警告">
          <strong>数据源警告</strong>
          <span>{warningText}</span>
        </section>
      ) : null}

      <section className="market-header" aria-labelledby="market-title">
        <div>
          <p className="eyebrow">C 阶段行情</p>
          <h2 id="market-title">
            {selectedInstrument.name} <span>{selectedInstrument.symbol}</span>
          </h2>
        </div>
        <form className="market-search" onSubmit={submitSearch}>
          <label>
            <span>标的搜索</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} />
          </label>
          <button type="submit" disabled={searchQuery.isFetching}>
            搜索
          </button>
        </form>
      </section>

      <section className="market-controls" aria-label="行情控制">
        <div className="segmented-control" role="group" aria-label="周期">
          {(Object.keys(resolutionLabels) as MarketResolution[]).map((item) => (
            <button
              key={item}
              type="button"
              className={resolution === item ? "selected" : ""}
              onClick={() => setResolution(item)}
            >
              {resolutionLabels[item]}
            </button>
          ))}
        </div>
        <label>
          <span>开始日期</span>
          <input
            type="date"
            value={startDate}
            onChange={(event) => setStartDate(event.target.value)}
          />
        </label>
        <label>
          <span>结束日期</span>
          <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
        </label>
        <label>
          <span>复权</span>
          <select
            value={adjustment}
            onChange={(event) => setAdjustment(event.target.value as Adjustment)}
          >
            <option value="none">{adjustmentLabels.none}</option>
            <option value="qfq">{adjustmentLabels.qfq}</option>
            <option value="hfq">{adjustmentLabels.hfq}</option>
          </select>
        </label>
      </section>

      {searchQuery.data && searchQuery.data.length > 0 ? (
        <section className="instrument-list" aria-label="搜索结果">
          {searchQuery.data.map((instrument) => (
            <button
              className={
                instrument.instrument_id === selectedInstrument.instrument_id ? "selected" : ""
              }
              type="button"
              key={instrument.instrument_id}
              onClick={() => setSelectedInstrument(instrument)}
            >
              {instrument.name} {instrument.symbol}
            </button>
          ))}
        </section>
      ) : null}

      {recentInstruments.length > 0 ? (
        <section className="instrument-list recent-list" aria-label="最近访问">
          {recentInstruments.map((instrument) => (
            <button
              className={
                instrument.instrument_id === selectedInstrument.instrument_id ? "selected" : ""
              }
              type="button"
              key={instrument.instrument_id}
              onClick={() => setSelectedInstrument(instrument)}
            >
              {instrument.name} {instrument.symbol}
            </button>
          ))}
        </section>
      ) : null}

      <section className="market-grid">
        <section className="market-chart-panel" aria-labelledby="chart-title">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">{resolutionLabels[resolution]}</p>
              <h3 id="chart-title">K 线与成交量</h3>
            </div>
            <div className="actions">
              <button
                className="secondary-button"
                type="button"
                onClick={() => setChartResetSignal((value) => value + 1)}
              >
                重置视图
              </button>
              <button type="button" onClick={() => setChartFullscreen((value) => !value)}>
                {chartFullscreen ? "退出全屏" : "全屏"}
              </button>
            </div>
          </div>
          {barsQuery.data ? (
            <MarketChart
              bars={barsQuery.data.bars}
              indicators={indicatorsQuery.data?.points}
              visibleIndicators={visibleIndicators}
              resetSignal={chartResetSignal}
              isFullscreen={chartFullscreen}
            />
          ) : (
            <div className="empty-state chart-empty-state" role="status">
              <strong>{barsQuery.error ? "行情数据暂不可用" : "正在加载行情数据"}</strong>
              <span>
                {barsQuery.error
                  ? barsQuery.error.message
                  : "正在连接本地后端和行情数据源"}
              </span>
            </div>
          )}
          <p className="chart-footnote">
            {barsQuery.data ? `${barsQuery.data.bars.length} 根` : "加载中"} · 支持十字光标、缩放、拖动
          </p>
        </section>

        <aside className="market-side" aria-label="行情基础信息">
          <InfoItem label="数据源" value={barsQuery.data?.provider ?? "akshare"} />
          <InfoItem label="最新价" value={formatNumber(quoteSummary.lastPrice)} />
          <InfoItem label="涨跌额" value={formatSignedNumber(quoteSummary.change)} />
          <InfoItem label="涨跌幅" value={formatPercent(quoteSummary.changePercent)} />
          <InfoItem label="报价时间" value={formatDateTime(quoteQuery.data?.as_of)} />
          <InfoItem label="市场" value={barsQuery.data?.market ?? selectedInstrument.market} />
          <InfoItem label="时区" value={barsQuery.data?.timezone ?? selectedInstrument.exchange_timezone} />
          <InfoItem label="周期" value={resolutionLabels[barsQuery.data?.resolution ?? resolution]} />
          <InfoItem label="复权" value={adjustmentLabels[adjustment]} />
          <InfoItem label="as_of" value={formatDateTime(barsQuery.data?.as_of)} />
          <InfoItem label="质量标记" value={formatFlags(barsQuery.data?.quality_flags)} />
        </aside>
      </section>

      <section className="indicator-panel" aria-labelledby="indicator-title">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">后端指标</p>
            <h3 id="indicator-title">最新指标</h3>
          </div>
          <strong>{formatDateTime(latestIndicator?.observed_at)}</strong>
        </div>
        {indicatorsQuery.error ? (
          <p className="error-text">{indicatorsQuery.error.message}</p>
        ) : (
          <>
            <IndicatorManager
              parameters={indicatorParameters}
              visibleIndicators={visibleIndicators}
              onParameterChange={updateIndicatorPeriod}
              onToggle={toggleIndicator}
            />
            <IndicatorGrid point={latestIndicator} parameters={indicatorsQuery.data?.parameters} />
          </>
        )}
      </section>

      <section className="watchlist-panel" aria-labelledby="watchlist-title">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">本地自选</p>
            <h3 id="watchlist-title">自选列表</h3>
          </div>
          <div className="actions">
            <button type="button" onClick={addSelectedInstrument} disabled={selectedInWatchlist}>
              加入自选
            </button>
            <button className="secondary-button" type="button" onClick={showExportJson}>
              导出 JSON
            </button>
          </div>
        </div>
        <p className="local-only">仅保存在当前浏览器</p>
        <div className="watchlist-items" aria-label="自选标的">
          {watchlistItems.length === 0 ? (
            <p className="empty-inline">暂无自选</p>
          ) : (
            watchlistItems.map((item) => (
              <div key={item.instrument_id}>
                <button type="button" onClick={() => setSelectedInstrument(item)}>
                  <strong>
                    {item.name} {item.symbol}
                  </strong>
                  <span>加入 {formatDateTime(item.added_at)}</span>
                </button>
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => removeInstrument(item.instrument_id)}
                >
                  移除
                </button>
              </div>
            ))
          )}
        </div>
        {exportText ? (
          <label className="json-area">
            <span>导出内容</span>
            <textarea readOnly value={exportText} rows={7} />
          </label>
        ) : null}
        <div className="import-row">
          <label className="json-area">
            <span>导入 JSON</span>
            <textarea
              value={importText}
              onChange={(event) => setImportText(event.target.value)}
              rows={7}
            />
          </label>
          <button type="button" onClick={submitImport} disabled={importText.trim().length === 0}>
            导入
          </button>
        </div>
        {importError ? <p className="error-text">{importError}</p> : null}
      </section>
    </main>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function IndicatorManager({
  parameters,
  visibleIndicators,
  onParameterChange,
  onToggle,
}: {
  parameters: IndicatorParameters;
  visibleIndicators: Record<IndicatorKey, boolean>;
  onParameterChange: (key: keyof IndicatorParameters, value: string) => void;
  onToggle: (key: IndicatorKey) => void;
}) {
  return (
    <div className="indicator-manager" aria-label="指标管理">
      <label>
        <input
          type="checkbox"
          checked={visibleIndicators.sma}
          onChange={() => onToggle("sma")}
        />
        <span>SMA</span>
        <input
          type="number"
          min={2}
          max={250}
          value={parameters.sma_period}
          onChange={(event) => onParameterChange("sma_period", event.target.value)}
        />
      </label>
      <label>
        <input
          type="checkbox"
          checked={visibleIndicators.ema}
          onChange={() => onToggle("ema")}
        />
        <span>EMA</span>
        <input
          type="number"
          min={2}
          max={250}
          value={parameters.ema_period}
          onChange={(event) => onParameterChange("ema_period", event.target.value)}
        />
      </label>
      <label>
        <input
          type="checkbox"
          checked={visibleIndicators.macd}
          onChange={() => onToggle("macd")}
        />
        <span>MACD</span>
        <input
          type="number"
          min={2}
          max={250}
          value={parameters.macd_fast_period}
          onChange={(event) => onParameterChange("macd_fast_period", event.target.value)}
          aria-label="MACD 快线"
        />
        <input
          type="number"
          min={3}
          max={500}
          value={parameters.macd_slow_period}
          onChange={(event) => onParameterChange("macd_slow_period", event.target.value)}
          aria-label="MACD 慢线"
        />
        <input
          type="number"
          min={2}
          max={250}
          value={parameters.macd_signal_period}
          onChange={(event) => onParameterChange("macd_signal_period", event.target.value)}
          aria-label="MACD 信号线"
        />
      </label>
      <label>
        <input
          type="checkbox"
          checked={visibleIndicators.rsi}
          onChange={() => onToggle("rsi")}
        />
        <span>RSI</span>
        <input
          type="number"
          min={2}
          max={250}
          value={parameters.rsi_period}
          onChange={(event) => onParameterChange("rsi_period", event.target.value)}
        />
      </label>
      <label>
        <input
          type="checkbox"
          checked={visibleIndicators.bollinger}
          onChange={() => onToggle("bollinger")}
        />
        <span>布林</span>
        <input
          type="number"
          min={2}
          max={250}
          value={parameters.bollinger_period}
          onChange={(event) => onParameterChange("bollinger_period", event.target.value)}
        />
        <input
          type="number"
          min={0.1}
          max={10}
          step={0.1}
          value={parameters.bollinger_multiplier}
          onChange={(event) => onParameterChange("bollinger_multiplier", event.target.value)}
          aria-label="布林倍数"
        />
      </label>
      <label>
        <input
          type="checkbox"
          checked={visibleIndicators.adx}
          onChange={() => onToggle("adx")}
        />
        <span>ADX</span>
        <input
          type="number"
          min={2}
          max={250}
          value={parameters.adx_period}
          onChange={(event) => onParameterChange("adx_period", event.target.value)}
        />
      </label>
    </div>
  );
}

function IndicatorGrid({
  point,
  parameters,
}: {
  point: IndicatorPoint | undefined;
  parameters: Indicators["parameters"] | undefined;
}) {
  const labels = parameters
    ? {
        sma: `SMA${parameters.sma_period}`,
        ema: `EMA${parameters.ema_period}`,
        macd: `MACD ${parameters.macd_fast_period}/${parameters.macd_slow_period}/${parameters.macd_signal_period}`,
        rsi: `RSI${parameters.rsi_period}`,
        bollinger: `布林 ${parameters.bollinger_period}`,
        adx: `ADX${parameters.adx_period}`,
      }
    : {
        sma: "SMA",
        ema: "EMA",
        macd: "MACD",
        rsi: "RSI",
        bollinger: "布林",
        adx: "ADX",
      };
  return (
    <div className="indicator-grid">
      <InfoItem label={labels.sma} value={formatNumber(point?.sma)} />
      <InfoItem label={labels.ema} value={formatNumber(point?.ema)} />
      <InfoItem label={labels.macd} value={formatNumber(point?.macd)} />
      <InfoItem label="MACD Signal" value={formatNumber(point?.macd_signal)} />
      <InfoItem label="MACD Hist" value={formatNumber(point?.macd_histogram)} />
      <InfoItem label={labels.rsi} value={formatNumber(point?.rsi)} />
      <InfoItem label={`${labels.bollinger}上轨`} value={formatNumber(point?.bollinger_upper)} />
      <InfoItem label={`${labels.bollinger}中轨`} value={formatNumber(point?.bollinger_middle)} />
      <InfoItem label={`${labels.bollinger}下轨`} value={formatNumber(point?.bollinger_lower)} />
      <InfoItem label={labels.adx} value={formatNumber(point?.adx)} />
    </div>
  );
}

function warningMessage(
  health: DataSourceHealth | undefined,
  bars: Bars | undefined,
  indicators: Indicators | undefined,
) {
  if (health && health.status !== "healthy") {
    return `akshare 当前为 ${health.status}，最后成功时间 ${formatDateTime(
      health.last_success_at,
    )}，缓存年龄 ${formatSeconds(health.stale_age_seconds)}。`;
  }
  const delayed = bars?.is_delayed || indicators?.is_delayed;
  if (delayed) {
    return `当前行情为延迟缓存，as_of ${formatDateTime(
      bars?.as_of ?? indicators?.as_of,
    )}，缓存年龄 ${formatSeconds(bars?.stale_age_seconds ?? indicators?.stale_age_seconds)}。`;
  }
  return null;
}

function quoteDetails(quote: Quote | undefined, bars: Bars | undefined) {
  const lastPrice = quote?.last_price ?? latestBar(bars)?.close_price ?? null;
  const previous = previousBar(bars)?.close_price ?? null;
  const change =
    lastPrice !== null && previous !== null ? Number(lastPrice) - Number(previous) : null;
  const changePercent =
    change !== null && previous !== null && Number(previous) !== 0
      ? change / Number(previous)
      : null;
  return { lastPrice, change, changePercent };
}

function latestBar(bars: Bars | undefined) {
  return bars?.bars[bars.bars.length - 1];
}

function previousBar(bars: Bars | undefined) {
  if (!bars || bars.bars.length < 2) {
    return undefined;
  }
  return bars.bars[bars.bars.length - 2];
}

function rememberInstrument(current: Instrument[], instrument: Instrument) {
  return [
    instrument,
    ...current.filter((item) => item.instrument_id !== instrument.instrument_id),
  ].slice(0, 6);
}

function daysBeforeInputDate(days: number) {
  const value = new Date();
  value.setDate(value.getDate() - days);
  return inputDate(value);
}

function inputDate(value: Date) {
  return value.toISOString().slice(0, 10);
}

function toApiDateTime(value: string) {
  return `${value}T00:00:00+08:00`;
}

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

function formatFlags(flags: string[] | undefined) {
  if (!flags || flags.length === 0) {
    return "无";
  }
  return flags.join(", ");
}

function formatSeconds(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "-";
  }
  return `${value} 秒`;
}

function formatNumber(value: string | number | null | undefined) {
  if (value === null || value === undefined) {
    return "-";
  }
  return Number(value).toFixed(4);
}

function formatSignedNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "-";
  }
  return `${value >= 0 ? "+" : ""}${value.toFixed(4)}`;
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "-";
  }
  return `${value >= 0 ? "+" : ""}${(value * 100).toFixed(2)}%`;
}

function loadMarketPreferences(): MarketPreferences | null {
  if (!canUseLocalStorage()) {
    return null;
  }
  const content = window.localStorage.getItem(MARKET_PREFERENCES_KEY);
  if (!content) {
    return null;
  }
  try {
    const parsed: unknown = JSON.parse(content);
    if (!isRecord(parsed) || parsed.version !== 1) {
      return null;
    }
    return {
      resolution: readResolution(parsed.resolution),
      adjustment: readAdjustment(parsed.adjustment),
      indicatorParameters: readIndicatorParameters(parsed.indicatorParameters),
      visibleIndicators: readVisibleIndicators(parsed.visibleIndicators),
      recentInstruments: readInstruments(parsed.recentInstruments).slice(0, 6),
    };
  } catch {
    return null;
  }
}

function saveMarketPreferences(preferences: MarketPreferences) {
  if (!canUseLocalStorage()) {
    return;
  }
  window.localStorage.setItem(
    MARKET_PREFERENCES_KEY,
    JSON.stringify({ version: 1, ...preferences }),
  );
}

function readResolution(value: unknown): MarketResolution {
  return value === "weekly" || value === "monthly" || value === "daily" ? value : "daily";
}

function readAdjustment(value: unknown): Adjustment {
  return value === "none" || value === "qfq" || value === "hfq" ? value : "qfq";
}

function readIndicatorParameters(value: unknown): IndicatorParameters {
  if (!isRecord(value)) {
    return defaultIndicatorParameters;
  }
  const parameters = {
    sma_period: readBoundedNumber(value.sma_period, 20),
    ema_period: readBoundedNumber(value.ema_period, 20),
    macd_fast_period: readBoundedNumber(value.macd_fast_period, 12),
    macd_slow_period: readBoundedNumber(value.macd_slow_period, 26),
    macd_signal_period: readBoundedNumber(value.macd_signal_period, 9),
    rsi_period: readBoundedNumber(value.rsi_period, 14),
    bollinger_period: readBoundedNumber(value.bollinger_period, 20),
    bollinger_multiplier: String(readBoundedDecimal(value.bollinger_multiplier, 2, 0.1, 10)),
    adx_period: readBoundedNumber(value.adx_period, 14),
  };
  if (parameters.macd_fast_period >= parameters.macd_slow_period) {
    parameters.macd_fast_period = defaultIndicatorParameters.macd_fast_period;
    parameters.macd_slow_period = defaultIndicatorParameters.macd_slow_period;
  }
  return parameters;
}

function readVisibleIndicators(value: unknown): Record<IndicatorKey, boolean> {
  if (!isRecord(value)) {
    return defaultVisibleIndicators;
  }
  return {
    sma: typeof value.sma === "boolean" ? value.sma : defaultVisibleIndicators.sma,
    ema: typeof value.ema === "boolean" ? value.ema : defaultVisibleIndicators.ema,
    bollinger:
      typeof value.bollinger === "boolean"
        ? value.bollinger
        : defaultVisibleIndicators.bollinger,
    macd: typeof value.macd === "boolean" ? value.macd : defaultVisibleIndicators.macd,
    rsi: typeof value.rsi === "boolean" ? value.rsi : defaultVisibleIndicators.rsi,
    adx: typeof value.adx === "boolean" ? value.adx : defaultVisibleIndicators.adx,
  };
}

function readInstruments(value: unknown): Instrument[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.flatMap((item) => {
    if (!isRecord(item)) {
      return [];
    }
    const instrument = {
      instrument_id: readOptionalString(item.instrument_id),
      symbol: readOptionalString(item.symbol),
      name: readOptionalString(item.name),
      market: readOptionalString(item.market),
      exchange_timezone: readOptionalString(item.exchange_timezone),
    };
    if (
      !instrument.instrument_id ||
      !instrument.symbol ||
      !instrument.name ||
      instrument.market !== "CN_A" ||
      !instrument.exchange_timezone
    ) {
      return [];
    }
    return [instrument as Instrument];
  });
}

function readBoundedNumber(value: unknown, fallback: number, min = 2, max = 500) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }
  return Math.min(max, Math.max(min, Math.trunc(parsed)));
}

function readBoundedDecimal(value: unknown, fallback: number, min: number, max: number) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }
  return Math.min(max, Math.max(min, parsed));
}

function readOptionalString(value: unknown) {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
}

function canUseLocalStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
