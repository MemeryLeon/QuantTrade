import { useQuery } from "@tanstack/react-query";
import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  getBars,
  getDataSourceHealth,
  getIndicators,
  searchInstruments,
  type Adjustment,
  type Bars,
  type DataSourceHealth,
  type Indicators,
  type Instrument,
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

export function MarketPage() {
  const [query, setQuery] = useState("平安");
  const [submittedQuery, setSubmittedQuery] = useState("平安");
  const [selectedInstrument, setSelectedInstrument] = useState<Instrument>(defaultInstrument);
  const [startDate, setStartDate] = useState(() => daysBeforeInputDate(180));
  const [endDate, setEndDate] = useState(() => inputDate(new Date()));
  const [adjustment, setAdjustment] = useState<Adjustment>("qfq");
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
  });
  const barsQuery = useQuery({
    queryKey: ["market-bars", selectedInstrument.instrument_id, startDate, endDate, adjustment],
    queryFn: () =>
      getBars({
        instrumentId: selectedInstrument.instrument_id,
        start: toApiDateTime(startDate),
        end: toApiDateTime(endDate),
        adjustment,
      }),
  });
  const indicatorsQuery = useQuery({
    queryKey: ["market-indicators", selectedInstrument.instrument_id, startDate, endDate, adjustment],
    queryFn: () =>
      getIndicators({
        instrumentId: selectedInstrument.instrument_id,
        start: toApiDateTime(startDate),
        end: toApiDateTime(endDate),
        adjustment,
      }),
  });

  useEffect(() => {
    const first = searchQuery.data?.[0];
    if (first) {
      setSelectedInstrument(first);
    }
  }, [searchQuery.data]);

  const indicatorPoints = indicatorsQuery.data?.points ?? [];
  const latestIndicator = indicatorPoints[indicatorPoints.length - 1];
  const warningText = warningMessage(healthQuery.data, barsQuery.data, indicatorsQuery.data);
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

      <section className="market-grid">
        <section className="market-chart-panel" aria-labelledby="chart-title">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">日线</p>
              <h3 id="chart-title">K 线与成交量</h3>
            </div>
            <strong>{barsQuery.data ? `${barsQuery.data.bars.length} 根` : "加载中"}</strong>
          </div>
          {barsQuery.data ? (
            <CandlestickChart bars={barsQuery.data.bars} indicators={indicatorsQuery.data?.points} />
          ) : null}
          {barsQuery.error ? <p className="error-text">{barsQuery.error.message}</p> : null}
        </section>

        <aside className="market-side" aria-label="行情基础信息">
          <InfoItem label="数据源" value={barsQuery.data?.provider ?? "akshare"} />
          <InfoItem label="市场" value={barsQuery.data?.market ?? selectedInstrument.market} />
          <InfoItem label="时区" value={barsQuery.data?.timezone ?? selectedInstrument.exchange_timezone} />
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
          <IndicatorGrid point={latestIndicator} parameters={indicatorsQuery.data?.parameters} />
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
                  {item.name} {item.symbol}
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

function CandlestickChart({
  bars,
  indicators,
}: {
  bars: Bar[];
  indicators: IndicatorPoint[] | undefined;
}) {
  const geometry = useMemo(() => chartGeometry(bars, indicators), [bars, indicators]);
  if (bars.length === 0 || !geometry) {
    return <p className="empty-state">暂无 K 线数据</p>;
  }

  return (
    <svg className="market-chart" viewBox="0 0 920 420" role="img" aria-label="K 线图">
      <rect x="0" y="0" width="920" height="420" rx="0" />
      <g className="chart-grid">
        {[0, 1, 2, 3].map((line) => (
          <line key={line} x1="48" x2="896" y1={42 + line * 72} y2={42 + line * 72} />
        ))}
      </g>
      <g className="volume-bars">
        {bars.map((bar, index) => {
          const x = geometry.x(index);
          const height = geometry.volumeHeight(bar.volume);
          return (
            <rect
              key={`volume-${bar.observed_at}`}
              x={x - geometry.candleWidth / 2}
              y={370 - height}
              width={geometry.candleWidth}
              height={height}
            />
          );
        })}
      </g>
      <g className="candles">
        {bars.map((bar, index) => {
          const x = geometry.x(index);
          const open = Number(bar.open_price);
          const close = Number(bar.close_price);
          const high = Number(bar.high_price);
          const low = Number(bar.low_price);
          const yOpen = geometry.y(open);
          const yClose = geometry.y(close);
          const colorClass = close >= open ? "up" : "down";
          return (
            <g key={bar.observed_at} className={colorClass}>
              <line x1={x} x2={x} y1={geometry.y(high)} y2={geometry.y(low)} />
              <rect
                x={x - geometry.candleWidth / 2}
                y={Math.min(yOpen, yClose)}
                width={geometry.candleWidth}
                height={Math.max(2, Math.abs(yClose - yOpen))}
              />
            </g>
          );
        })}
      </g>
      {geometry.smaPath ? <path className="indicator-line sma-line" d={geometry.smaPath} /> : null}
      {geometry.emaPath ? <path className="indicator-line ema-line" d={geometry.emaPath} /> : null}
      {geometry.bollingerUpperPath ? (
        <path className="indicator-line bollinger-line" d={geometry.bollingerUpperPath} />
      ) : null}
      {geometry.bollingerLowerPath ? (
        <path className="indicator-line bollinger-line" d={geometry.bollingerLowerPath} />
      ) : null}
      <text x="48" y="400">
        {new Date(bars[0].observed_at).toLocaleDateString()} -{" "}
        {new Date(bars[bars.length - 1].observed_at).toLocaleDateString()}
      </text>
    </svg>
  );
}

function chartGeometry(bars: Bar[], indicators: IndicatorPoint[] | undefined) {
  if (bars.length === 0) {
    return null;
  }
  const indicatorValues = (indicators ?? []).flatMap((point) =>
    [
      point.sma,
      point.ema,
      point.bollinger_upper,
      point.bollinger_lower,
      point.bollinger_middle,
    ]
      .filter((value): value is string => value !== null)
      .map(Number),
  );
  const prices = bars.flatMap((bar) => [
    Number(bar.high_price),
    Number(bar.low_price),
    Number(bar.open_price),
    Number(bar.close_price),
  ]);
  const min = Math.min(...prices, ...indicatorValues);
  const max = Math.max(...prices, ...indicatorValues);
  const range = max === min ? 1 : max - min;
  const maxVolume = Math.max(...bars.map((bar) => bar.volume), 1);
  const step = bars.length > 1 ? 848 / (bars.length - 1) : 16;
  const candleWidth = Math.max(4, Math.min(14, step * 0.58));
  const x = (index: number) => 48 + index * step;
  const y = (value: number) => 292 - ((value - min) / range) * 250;
  const linePath = (key: keyof IndicatorPoint) => {
    const segments = (indicators ?? [])
      .map((point, index) => ({ value: point[key], index }))
      .filter((entry): entry is { value: string; index: number } => entry.value !== null)
      .map((entry, pathIndex) => `${pathIndex === 0 ? "M" : "L"}${x(entry.index)},${y(Number(entry.value))}`);
    return segments.length > 0 ? segments.join(" ") : null;
  };

  return {
    candleWidth,
    x,
    y,
    volumeHeight: (volume: number) => Math.max(2, (volume / maxVolume) * 76),
    smaPath: linePath("sma"),
    emaPath: linePath("ema"),
    bollingerUpperPath: linePath("bollinger_upper"),
    bollingerLowerPath: linePath("bollinger_lower"),
  };
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
