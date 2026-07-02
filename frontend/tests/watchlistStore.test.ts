import { beforeEach, describe, expect, it } from "vitest";

import {
  parseWatchlistDocument,
  useWatchlistStore,
  WATCHLIST_STORAGE_KEY,
} from "../src/stores/watchlistStore";

const instrument = {
  instrument_id: "CN_A:000001",
  symbol: "000001",
  name: "平安银行",
  market: "CN_A",
  exchange_timezone: "Asia/Shanghai",
};

describe("watchlist store", () => {
  beforeEach(() => {
    window.localStorage.clear();
    useWatchlistStore.setState({ items: [] });
  });

  it("persists a versioned local watchlist", () => {
    useWatchlistStore.getState().addInstrument(instrument);

    const stored = window.localStorage.getItem(WATCHLIST_STORAGE_KEY);
    expect(stored).not.toBeNull();
    const items = parseWatchlistDocument(stored ?? "").items;
    expect(items[0]).toMatchObject(instrument);
    expect(Date.parse(items[0].added_at)).not.toBeNaN();
  });

  it("imports valid json and rejects invalid json", () => {
    useWatchlistStore
      .getState()
      .importJson(JSON.stringify({ version: 1, items: [instrument, instrument] }));

    const items = useWatchlistStore.getState().items;
    expect(items).toHaveLength(1);
    expect(items[0]).toMatchObject(instrument);
    expect(Date.parse(items[0].added_at)).not.toBeNaN();
    expect(() => useWatchlistStore.getState().importJson("{bad")).toThrow("导入 JSON 格式不正确");
    expect(() => useWatchlistStore.getState().importJson(JSON.stringify({ version: 2 }))).toThrow(
      "quanttrade.watchlist.v1",
    );
  });
});
