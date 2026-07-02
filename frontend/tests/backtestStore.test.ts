import { describe, expect, it } from "vitest";

import { useBacktestStore } from "../src/stores/backtestStore";

describe("backtest ui store", () => {
  it("tracks the current mock backtest job id", () => {
    useBacktestStore.getState().setCurrentJobId("job-1");

    expect(useBacktestStore.getState().currentJobId).toBe("job-1");

    useBacktestStore.getState().setCurrentJobId(null);

    expect(useBacktestStore.getState().currentJobId).toBeNull();
  });
});
