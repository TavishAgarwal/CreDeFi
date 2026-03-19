"use client";

import { type ReactNode } from "react";
import { useHydrateAuth } from "@/hooks/use-hydrate-auth";
import { useWalletEvents } from "@/hooks/use-wallet-events";

/**
 * Root client-side provider that bootstraps:
 *  - Auth session hydration (reads JWT from localStorage)
 *  - MetaMask event listeners (account / chain changes)
 *
 * Wrap the app layout's children with this component.
 */
export function AppProvider({ children }: { children: ReactNode }) {
  useHydrateAuth();
  useWalletEvents();
  return <>{children}</>;
}
