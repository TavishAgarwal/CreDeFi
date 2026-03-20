"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { Menu, X, Zap, Wallet, Eye, Download } from "lucide-react"
import { cn } from "@/lib/utils"
import { useWalletStore } from "@/stores/wallet-store"
import { useAuthStore } from "@/stores/auth-store"
import { useDemoStore } from "@/stores/demo-store"
import { isMetaMaskInstalled } from "@/lib/wallet"

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/platforms", label: "Platforms" },
  { href: "/loan", label: "Request Loan" },
  { href: "/graph", label: "Trust Graph" },
  { href: "/lender", label: "Lender" },
  { href: "/transactions", label: "Transactions" },
]

function truncateAddress(addr: string) {
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`
}

export function Navbar() {
  const [open, setOpen] = useState(false)
  const [showMetaMaskDialog, setShowMetaMaskDialog] = useState(false)
  const pathname = usePathname()
  const router = useRouter()
  const { address, status, connect, disconnect } = useWalletStore()
  const { isAuthenticated, user, logout } = useAuthStore()
  const { isDemo, exit: exitDemo, enter: enterDemo } = useDemoStore()

  return (
    <>
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 glass-card">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center orange-glow group-hover:scale-105 transition-transform">
              <Zap className="w-4 h-4 text-primary-foreground" />
            </div>
            <span className="font-bold text-xl tracking-tight">
              Cre<span className="text-primary">DeFi</span>
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                  pathname === link.href
                    ? "text-primary bg-primary/10"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                )}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-3">
            {isDemo && (
              <>
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 text-amber-400 text-xs font-semibold">
                  <Eye className="w-3 h-3" />
                  Demo Mode
                </div>
                <button
                  onClick={exitDemo}
                  className="px-3 py-1.5 rounded-lg border border-border text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                >
                  Exit Demo
                </button>
              </>
            )}
            {address ? (
              <>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-border text-xs text-muted-foreground">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  {truncateAddress(address)}
                </div>
                {isAuthenticated && user?.display_name && (
                  <span className="text-xs text-muted-foreground">
                    {user.display_name}
                  </span>
                )}
                <button
                  onClick={() => { disconnect(); logout(); }}
                  className="px-3 py-1.5 rounded-lg border border-border text-sm text-muted-foreground hover:text-destructive hover:border-destructive/30 transition-colors"
                >
                  Disconnect
                </button>
              </>
            ) : !isDemo ? (
              <button
                onClick={() => {
                  if (!isMetaMaskInstalled()) {
                    setShowMetaMaskDialog(true)
                  } else {
                    connect()
                  }
                }}
                disabled={status === "connecting"}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                <Wallet className="w-4 h-4" />
                {status === "connecting" ? "Connecting..." : "Connect Wallet"}
              </button>
            ) : null}
          </div>

          <button
            className="md:hidden p-2 rounded-md text-muted-foreground hover:text-foreground"
            onClick={() => setOpen(!open)}
            aria-label="Toggle menu"
          >
            {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {open && (
        <div className="md:hidden border-t border-border bg-background/95 backdrop-blur-xl">
          <div className="px-4 py-4 flex flex-col gap-1">
            {isDemo && (
              <div className="flex items-center justify-between mb-2 px-3 py-2 rounded-md bg-amber-500/10 border border-amber-500/20">
                <div className="flex items-center gap-1.5 text-amber-400 text-xs font-semibold">
                  <Eye className="w-3 h-3" />
                  Demo Mode
                </div>
                <button onClick={exitDemo} className="text-xs text-muted-foreground hover:text-foreground">
                  Exit
                </button>
              </div>
            )}
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className={cn(
                  "px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  pathname === link.href
                    ? "text-primary bg-primary/10"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                )}
              >
                {link.label}
              </Link>
            ))}
            {address ? (
              <div className="mt-2 flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                {truncateAddress(address)}
              </div>
            ) : !isDemo ? (
              <button
                onClick={() => {
                  if (!isMetaMaskInstalled()) {
                    setShowMetaMaskDialog(true)
                  } else {
                    connect()
                  }
                  setOpen(false)
                }}
                disabled={status === "connecting"}
                className="mt-2 w-full px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-50"
              >
                {status === "connecting" ? "Connecting..." : "Connect Wallet"}
              </button>
            ) : null}
          </div>
        </div>
      )}
    </header>

    {/* MetaMask not-installed dialog */}
    {showMetaMaskDialog && (
      <div className="fixed inset-0 z-[60] flex items-center justify-center">
        <div
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          onClick={() => setShowMetaMaskDialog(false)}
        />
        <div className="relative w-full max-w-md mx-4 glass-card rounded-2xl border border-primary/20 p-8 animate-in fade-in zoom-in-95 duration-200">
          <button
            onClick={() => setShowMetaMaskDialog(false)}
            className="absolute top-4 right-4 w-8 h-8 rounded-lg bg-secondary flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
          <div className="flex flex-col items-center text-center gap-5">
            <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
              <Wallet className="w-8 h-8 text-amber-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-foreground mb-2">MetaMask Not Detected</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                To connect your wallet, you need the MetaMask browser extension installed. You can also explore the full app with demo data.
              </p>
            </div>
            <div className="flex flex-col gap-3 w-full">
              <a
                href="https://metamask.io/download/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 w-full px-6 py-3 rounded-xl bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-all hover:shadow-lg hover:shadow-primary/20 active:scale-95"
              >
                <Download className="w-4 h-4" />
                Install MetaMask
              </a>
              <button
                onClick={() => {
                  enterDemo()
                  setShowMetaMaskDialog(false)
                  router.push("/dashboard")
                }}
                className="inline-flex items-center justify-center gap-2 w-full px-6 py-3 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-400 font-semibold hover:bg-amber-500/20 transition-colors"
              >
                <Eye className="w-4 h-4" />
                Try Demo Instead
              </button>
            </div>
            <p className="text-xs text-muted-foreground">
              MetaMask is a free browser extension for managing crypto wallets.
            </p>
          </div>
        </div>
      </div>
    )}
    </>
  )
}
