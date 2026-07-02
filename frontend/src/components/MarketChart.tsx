import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  HistogramSeries,
  LineSeries,
  createChart,
  type HistogramData,
  type IChartApi,
  type ISeriesApi,
  type LineData,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useMemo, useRef } from "react";

import type { Bars, Indicators } from "../services/market";

type Bar = Bars["bars"][number];
type IndicatorPoint = Indicators["points"][number];

export type IndicatorKey = "sma" | "ema" | "bollinger" | "macd" | "rsi" | "adx";

type MarketChartProps = {
  bars: Bar[];
  indicators: IndicatorPoint[] | undefined;
  visibleIndicators: Record<IndicatorKey, boolean>;
  resetSignal: number;
  isFullscreen: boolean;
};

export function MarketChart({
  bars,
  indicators,
  visibleIndicators,
  resetSignal,
  isFullscreen,
}: MarketChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  const chartData = useMemo(() => toChartData(bars, indicators), [bars, indicators]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }
    const chart = createChart(container, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#0b1117" },
        textColor: "#9aa7b5",
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: "#18222e" },
        horzLines: { color: "#18222e" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: "#223041",
      },
      timeScale: {
        borderColor: "#223041",
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: true,
      handleScale: true,
    });
    const candles = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });
    const volume = chart.addSeries(HistogramSeries, {
      color: "#334155",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    chart.priceScale("volume").applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });
    chartRef.current = chart;
    seriesRef.current = candles;
    volumeRef.current = volume;
    return () => {
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
      volumeRef.current = null;
    };
  }, []);

  useEffect(() => {
    const chart = chartRef.current;
    const candles = seriesRef.current;
    const volume = volumeRef.current;
    if (!chart || !candles || !volume) {
      return;
    }
    candles.setData(chartData.candles);
    volume.setData(chartData.volume);
    const overlays = createIndicatorSeries(chart, chartData.indicators, visibleIndicators);
    overlays.forEach(({ series, data }) => series.setData(data));
    chart.timeScale().fitContent();
    return () => {
      overlays.forEach(({ series }) => removeSeries(chart, series));
    };
  }, [chartData, visibleIndicators]);

  useEffect(() => {
    chartRef.current?.timeScale().fitContent();
  }, [resetSignal]);

  if (bars.length === 0) {
    return <p className="empty-state">暂无 K 线数据</p>;
  }

  return (
    <div
      className={isFullscreen ? "market-chart-frame fullscreen-chart" : "market-chart-frame"}
      aria-label="K 线图，支持十字光标、缩放和拖动"
    >
      <div ref={containerRef} className="market-chart-canvas" />
    </div>
  );
}

function toChartData(bars: Bar[], indicators: IndicatorPoint[] | undefined) {
  return {
    candles: bars.map((bar) => ({
      time: toTimestamp(bar.observed_at),
      open: Number(bar.open_price),
      high: Number(bar.high_price),
      low: Number(bar.low_price),
      close: Number(bar.close_price),
    })),
    volume: bars.map((bar) => ({
      time: toTimestamp(bar.observed_at),
      value: bar.volume,
      color: Number(bar.close_price) >= Number(bar.open_price) ? "#14532d" : "#7f1d1d",
    })),
    indicators: indicators ?? [],
  };
}

function createIndicatorSeries(
  chart: IChartApi,
  indicators: IndicatorPoint[],
  visible: Record<IndicatorKey, boolean>,
) {
  const data = chartDataFromSeries(indicators);
  const overlays: Array<{
    series: ISeriesApi<"Line"> | ISeriesApi<"Histogram">;
    data: LineData[] | HistogramData[];
  }> = [];
  if (visible.sma) {
    overlays.push({
      series: chart.addSeries(LineSeries, { color: "#38bdf8", lineWidth: 2, title: "SMA" }),
      data: data("sma"),
    });
  }
  if (visible.ema) {
    overlays.push({
      series: chart.addSeries(LineSeries, { color: "#f59e0b", lineWidth: 2, title: "EMA" }),
      data: data("ema"),
    });
  }
  if (visible.bollinger) {
    overlays.push({
      series: chart.addSeries(LineSeries, { color: "#a78bfa", lineWidth: 1, title: "BOLL U" }),
      data: data("bollinger_upper"),
    });
    overlays.push({
      series: chart.addSeries(LineSeries, { color: "#a78bfa", lineWidth: 1, title: "BOLL L" }),
      data: data("bollinger_lower"),
    });
  }
  if (visible.macd) {
    overlays.push({
      series: chart.addSeries(HistogramSeries, {
        color: "#64748b",
        priceScaleId: "macd",
        title: "MACD",
      }),
      data: data("macd_histogram"),
    });
    chart.priceScale("macd").applyOptions({ scaleMargins: { top: 0.72, bottom: 0.12 } });
  }
  if (visible.rsi) {
    overlays.push({
      series: chart.addSeries(LineSeries, {
        color: "#2dd4bf",
        lineWidth: 1,
        priceScaleId: "oscillator",
        title: "RSI",
      }),
      data: data("rsi"),
    });
  }
  if (visible.adx) {
    overlays.push({
      series: chart.addSeries(LineSeries, {
        color: "#f97316",
        lineWidth: 1,
        priceScaleId: "oscillator",
        title: "ADX",
      }),
      data: data("adx"),
    });
  }
  if (visible.rsi || visible.adx) {
    chart.priceScale("oscillator").applyOptions({ scaleMargins: { top: 0.64, bottom: 0.22 } });
  }
  return overlays;
}

function chartDataFromSeries(source: IndicatorPoint[]) {
  return (key: keyof IndicatorPoint) =>
    source
      .map((point) => ({ time: toTimestamp(point.observed_at), value: point[key] }))
      .filter((point): point is { time: UTCTimestamp; value: string } => point.value !== null)
      .map((point) => ({ time: point.time, value: Number(point.value) }));
}

function toTimestamp(value: string): UTCTimestamp {
  return Math.floor(new Date(value).getTime() / 1000) as UTCTimestamp;
}

function removeSeries(chart: IChartApi, series: ISeriesApi<"Line"> | ISeriesApi<"Histogram">) {
  try {
    chart.removeSeries(series);
  } catch {
    // React StrictMode can run cleanup after the chart instance has already removed child series.
  }
}
