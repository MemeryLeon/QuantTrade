import { create } from "zustand";

import type { Instrument } from "../services/market";

export const WATCHLIST_STORAGE_KEY = "quanttrade.watchlist.v1";

export type WatchlistItem = Instrument & {
  added_at: string;
};

type WatchlistDocument = {
  version: 1;
  items: WatchlistItem[];
};

type WatchlistState = {
  items: WatchlistItem[];
  addInstrument: (instrument: Instrument) => void;
  removeInstrument: (instrumentId: string) => void;
  exportJson: () => string;
  importJson: (content: string) => void;
};

export const useWatchlistStore = create<WatchlistState>((set, get) => ({
  items: loadWatchlist(),
  addInstrument: (instrument) => {
    set((state) => {
      if (state.items.some((item) => item.instrument_id === instrument.instrument_id)) {
        return state;
      }
      const items = [...state.items, toWatchlistItem(instrument)];
      saveWatchlist(items);
      return { items };
    });
  },
  removeInstrument: (instrumentId) => {
    set((state) => {
      const items = state.items.filter((item) => item.instrument_id !== instrumentId);
      saveWatchlist(items);
      return { items };
    });
  },
  exportJson: () => {
    return JSON.stringify({ version: 1, items: get().items } satisfies WatchlistDocument, null, 2);
  },
  importJson: (content) => {
    const document = parseWatchlistDocument(content);
    saveWatchlist(document.items);
    set({ items: document.items });
  },
}));

export function parseWatchlistDocument(content: string): WatchlistDocument {
  let parsed: unknown;
  try {
    parsed = JSON.parse(content);
  } catch (error) {
    throw new Error("导入 JSON 格式不正确");
  }
  if (!isRecord(parsed) || parsed.version !== 1 || !Array.isArray(parsed.items)) {
    throw new Error("导入文件不是 quanttrade.watchlist.v1");
  }
  const items = parsed.items.map((item) => {
    if (!isRecord(item)) {
      throw new Error("自选项结构不正确");
    }
    const instrument = toWatchlistItem({
      instrument_id: readString(item, "instrument_id"),
      symbol: readString(item, "symbol"),
      name: readString(item, "name"),
      market: readString(item, "market"),
      exchange_timezone: readString(item, "exchange_timezone"),
    });
    if (instrument.market !== "CN_A") {
      throw new Error("当前仅支持 CN_A 自选");
    }
    if (instrument.exchange_timezone.length === 0) {
      throw new Error("自选项缺少交易所时区");
    }
    return instrument;
  });
  return { version: 1, items: dedupeItems(items) };
}

function loadWatchlist(): WatchlistItem[] {
  if (!canUseLocalStorage()) {
    return [];
  }
  const content = window.localStorage.getItem(WATCHLIST_STORAGE_KEY);
  if (!content) {
    return [];
  }
  try {
    return parseWatchlistDocument(content).items;
  } catch {
    return [];
  }
}

function saveWatchlist(items: WatchlistItem[]) {
  if (!canUseLocalStorage()) {
    return;
  }
  window.localStorage.setItem(
    WATCHLIST_STORAGE_KEY,
    JSON.stringify({ version: 1, items: dedupeItems(items) } satisfies WatchlistDocument),
  );
}

function dedupeItems(items: WatchlistItem[]) {
  const seen = new Set<string>();
  return items.filter((item) => {
    if (seen.has(item.instrument_id)) {
      return false;
    }
    seen.add(item.instrument_id);
    return true;
  });
}

function toWatchlistItem(instrument: Instrument): WatchlistItem {
  return {
    ...instrument,
    added_at: new Date().toISOString(),
  };
}

function canUseLocalStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readString(record: Record<string, unknown>, key: string) {
  const value = record[key];
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`自选项缺少 ${key}`);
  }
  return value.trim();
}
