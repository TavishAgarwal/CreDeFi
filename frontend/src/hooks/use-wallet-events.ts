"use client";

import { useEffect } from "react";
import { useWalletStore } from "@/stores/wallet-store";
import { onAccountsChanged, onChainChanged } from "@/lib/wallet";

/**
 * Subscribes to MetaMask account/chain change events and
 * syncs them into the wallet Zustand store.
 * Mount this once near the app root.
 */
export function useWalletEvents() {
  const handleAccountsChanged = useWalletStore(
    (s) => s.handleAccountsChanged
  );
  const handleChainChanged = useWalletStore((s) => s.handleChainChanged);

  useEffect(() => {
    const unsubAccounts = onAccountsChanged(handleAccountsChanged);
    const unsubChain = onChainChanged(handleChainChanged);
    return () => {
      unsubAccounts();
      unsubChain();
    };
  }, [handleAccountsChanged, handleChainChanged]);
}
