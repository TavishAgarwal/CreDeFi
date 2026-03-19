"use client";

import { useWalletStore } from "@/stores/wallet-store";
import { Wallet, Play, Shield, ArrowRight } from "lucide-react";

/**
 * Gates all (app) pages behind wallet connection or demo mode.
 * Shows a premium connect screen if neither is active.
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { address, demoMode, status, connect, enableDemo, error, clearError } =
    useWalletStore();

  const hasAccess = !!address || demoMode;

  if (hasAccess) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4">
      <div className="w-full max-w-md text-center">
        {/* Icon */}
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-brand/20 to-amber-500/10 border border-brand/20">
          <Shield className="h-10 w-10 text-brand" />
        </div>

        {/* Heading */}
        <h1 className="text-2xl font-bold tracking-tight">
          Connect to <span className="text-brand">CreDeFi</span>
        </h1>
        <p className="mt-3 text-sm text-gray-400 leading-relaxed max-w-sm mx-auto">
          Connect your MetaMask wallet to access your dashboard, manage loans,
          and track your trust score. Or try our demo to explore.
        </p>

        {/* Error */}
        {error && (
          <div className="mt-4 rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
            {error}
            <button
              onClick={clearError}
              className="ml-2 text-red-300 underline hover:text-red-200"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Buttons */}
        <div className="mt-8 space-y-3">
          <button
            onClick={connect}
            disabled={status === "connecting"}
            className="flex w-full items-center justify-center gap-2.5 rounded-xl bg-brand px-5 py-3.5 text-sm font-semibold text-gray-950 transition-all duration-200 hover:bg-amber-400 hover:shadow-lg hover:shadow-brand/25 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Wallet className="h-4.5 w-4.5" />
            {status === "connecting" ? "Connecting..." : "Connect MetaMask Wallet"}
            {status !== "connecting" && <ArrowRight className="h-4 w-4" />}
          </button>

          <button
            onClick={enableDemo}
            className="flex w-full items-center justify-center gap-2.5 rounded-xl border border-white/10 bg-white/[0.03] px-5 py-3.5 text-sm font-medium text-gray-300 transition-all duration-200 hover:bg-white/[0.07] hover:border-brand/30 hover:text-brand"
          >
            <Play className="h-4 w-4" />
            Try Demo Mode
          </button>
        </div>

        {/* Fine print */}
        <p className="mt-6 text-[11px] text-gray-600">
          Demo mode uses sample data. No wallet or sign-in required.
        </p>
      </div>
    </div>
  );
}
