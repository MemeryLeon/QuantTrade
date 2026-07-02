import { create } from "zustand";

type BacktestUiState = {
  currentJobId: string | null;
  setCurrentJobId: (jobId: string | null) => void;
};

export const useBacktestStore = create<BacktestUiState>((set) => ({
  currentJobId: null,
  setCurrentJobId: (jobId) => set({ currentJobId: jobId }),
}));
