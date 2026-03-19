"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, Wallet } from "lucide-react";
import { useWalletStore } from "@/stores/wallet-store";
import { useAuthStore } from "@/stores/auth-store";

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
  const { address, status, connect } = useWalletStore();
  const { isAuthenticated, user } = useAuthStore();

  return (
    <nav className="sticky top-0 z-50 border-b border-surface-border bg-gray-950/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-sm font-bold text-gray-950">
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
                  key={link.href}
                  href={link.href}
                  className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    active
                      ? "text-brand"
                      : "text-gray-400 hover:text-gray-100"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button className="relative text-gray-400 transition-colors hover:text-gray-100">
            <Bell className="h-5 w-5" />
          </button>

          {address ? (
            <div className="flex items-center gap-2 rounded-full border border-surface-border bg-surface px-3 py-1.5">
              <div className="h-6 w-6 rounded-full bg-brand" />
              <span className="text-sm font-medium">
                {truncateAddress(address)}
              </span>
            </div>
          ) : (
            <button
              onClick={connect}
              disabled={status === "connecting"}
              className="flex items-center gap-2 rounded-full bg-brand px-4 py-1.5 text-sm font-semibold text-gray-950 transition-colors hover:bg-amber-400 disabled:opacity-50"
            >
              <Wallet className="h-4 w-4" />
              {status === "connecting" ? "Connecting..." : "Connect Wallet"}
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
