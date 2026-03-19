"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, Wallet, X } from "lucide-react";
import { useWalletStore } from "@/stores/wallet-store";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/loans", label: "Loans" },
  { href: "/connections", label: "Connections" },
  { href: "/transactions", label: "Transactions" },
];

function truncateAddress(addr: string) {
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

export function Navbar() {
  const pathname = usePathname();
  const { address, status, connect, demoMode, disableDemo, disconnect } = useWalletStore();

  return (
    <nav className="sticky top-0 z-50 border-b border-white/[0.06] bg-[#0B0F1A]/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2 group">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-sm font-bold text-gray-950 transition-transform duration-200 group-hover:scale-105">
              C
            </span>
            <span className="text-lg font-bold">
              Cre<span className="text-brand">DeFi</span>
            </span>
          </Link>

          <div className="hidden items-center gap-1 md:flex">
            {NAV_LINKS.map((link) => {
              const active = pathname.startsWith(link.href);
              return (
                <Link
                  key={link.label}
                  href={link.href}
                  className={`relative rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-200 ${
                    active
                      ? "text-brand"
                      : "text-gray-400 hover:text-gray-100"
                  }`}
                >
                  {link.label}
                  {active && (
                    <span className="absolute bottom-0 left-3 right-3 h-0.5 rounded-full bg-brand" />
                  )}
                </Link>
              );
            })}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button className="relative text-gray-500 transition-colors duration-200 hover:text-gray-100">
            <Bell className="h-5 w-5" />
          </button>

          {/* Demo mode badge */}
          {demoMode && (
            <div className="flex items-center gap-2 rounded-full border border-brand/30 bg-brand/10 px-3 py-1.5">
              <span className="text-xs font-semibold text-brand">Demo Mode</span>
              <button
                onClick={disableDemo}
                className="flex h-4 w-4 items-center justify-center rounded-full bg-brand/20 text-brand hover:bg-brand/40 transition-colors"
                title="Exit Demo"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          )}

          {/* Wallet connected (real) */}
          {address && !demoMode ? (
            <button
              onClick={disconnect}
              className="flex items-center gap-2 rounded-full border border-surface-border bg-surface px-3 py-1.5 transition-colors hover:border-red-500/30 group"
              title="Disconnect wallet"
            >
              <div className="h-6 w-6 rounded-full bg-gradient-to-br from-brand to-amber-400" />
              <span className="text-sm font-medium group-hover:text-red-400 transition-colors">
                {truncateAddress(address)}
              </span>
            </button>
          ) : !demoMode ? (
            <button
              onClick={connect}
              disabled={status === "connecting"}
              className="flex items-center gap-2 rounded-full bg-brand px-4 py-1.5 text-sm font-semibold text-gray-950 transition-all duration-200 hover:bg-amber-400 hover:shadow-lg hover:shadow-brand/20 disabled:opacity-50"
            >
              <Wallet className="h-4 w-4" />
              {status === "connecting" ? "Connecting..." : "Connect Wallet"}
            </button>
          ) : null}
        </div>
      </div>
    </nav>
  );
}
