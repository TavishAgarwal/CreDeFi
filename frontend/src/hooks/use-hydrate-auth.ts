"use client";

import { useEffect, useRef } from "react";
import { useAuthStore } from "@/stores/auth-store";

/**
 * Attempts to restore the authenticated session from a stored JWT
 * on first mount.  Safe to call multiple times — runs only once.
 */
export function useHydrateAuth() {
  const hydrate = useAuthStore((s) => s.hydrate);
  const called = useRef(false);

  useEffect(() => {
    if (called.current) return;
    called.current = true;
    hydrate();
  }, [hydrate]);
}
