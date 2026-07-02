import { apiClient } from "../api/client";
import type { components } from "../api/generated/schema";

export type Instrument = components["schemas"]["InstrumentResponse"];
export type Bars = components["schemas"]["BarsResponse"];
export type Quote = components["schemas"]["QuoteResponse"];
export type Indicators = components["schemas"]["IndicatorsResponse"];
export type DataSourceHealth = components["schemas"]["DataSourceHealthResponse"];
export type Adjustment = Bars["adjustment"];
export type MarketResolution = Bars["resolution"];
export type IndicatorParameters = Indicators["parameters"];

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

export async function searchInstruments(query: string): Promise<Instrument[]> {
  const { data, error } = await apiClient.GET("/market/instruments/search", {
    params: { query: { query } },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error));
  }
  return data.instruments;
}

export async function getBars(params: {
  instrumentId: string;
  start: string;
  end: string;
  resolution: MarketResolution;
  adjustment: Adjustment;
}): Promise<Bars> {
  const { data, error } = await apiClient.GET("/market/bars", {
    params: {
      query: {
        instrument_id: params.instrumentId,
        start: params.start,
        end: params.end,
        resolution: params.resolution,
        adjustment: params.adjustment,
      },
    },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error));
  }
  return data;
}

export async function getQuote(instrumentId: string): Promise<Quote> {
  const { data, error } = await apiClient.GET("/market/quote", {
    params: { query: { instrument_id: instrumentId } },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error));
  }
  return data;
}

export async function getIndicators(params: {
  instrumentId: string;
  start: string;
  end: string;
  resolution: MarketResolution;
  adjustment: Adjustment;
  parameters: IndicatorParameters;
}): Promise<Indicators> {
  const { data, error } = await apiClient.GET("/market/indicators", {
    params: {
      query: {
        instrument_id: params.instrumentId,
        start: params.start,
        end: params.end,
        resolution: params.resolution,
        adjustment: params.adjustment,
        sma_period: params.parameters.sma_period,
        ema_period: params.parameters.ema_period,
        macd_fast_period: params.parameters.macd_fast_period,
        macd_slow_period: params.parameters.macd_slow_period,
        macd_signal_period: params.parameters.macd_signal_period,
        rsi_period: params.parameters.rsi_period,
        bollinger_period: params.parameters.bollinger_period,
        bollinger_multiplier: params.parameters.bollinger_multiplier,
        adx_period: params.parameters.adx_period,
      },
    },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error));
  }
  return data;
}

export async function getDataSourceHealth(): Promise<DataSourceHealth> {
  const { data, error } = await apiClient.GET("/market/data-sources/{provider}/health", {
    params: { path: { provider: "akshare" } },
  });
  if (error || !data) {
    throw new Error(apiErrorMessage(error));
  }
  return data;
}
