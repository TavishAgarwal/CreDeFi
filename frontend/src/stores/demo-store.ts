import { create } from "zustand";

interface DemoState {
  isDemo: boolean;
  enter: () => void;
  exit: () => void;
}

export const useDemoStore = create<DemoState>((set) => ({
  isDemo: false,
  enter: () => set({ isDemo: true }),
  exit: () => set({ isDemo: false }),
}));
