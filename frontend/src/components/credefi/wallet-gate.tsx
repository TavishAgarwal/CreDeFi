"use client"

import { type ReactNode } from "react"
import Link from "next/link"
import { Wallet, Zap, Eye, ShieldCheck, ArrowRight } from "lucide-react"
import { useWalletStore } from "@/stores/wallet-store"
import { useDemoStore } from "@/stores/demo-store"

interface WalletGateProps {
  children: ReactNode
}

export function WalletGate({ children }: WalletGateProps) {
  const { address, status, connect } = useWalletStore()
  const { isDemo, enter } = useDemoStore()

  if (address || isDemo) {
    return <>{children}</>
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-24 flex flex-col items-center gap-8 text-center">
      <div className="w-20 h-20 rounded-3xl bg-primary/10 border border-primary/20 flex items-center justify-center orange-glow">
        <Wallet className="w-10 h-10 text-primary" />
      </div>

      <div>
        <h1 className="text-3xl font-bold text-foreground">Connect Your Wallet</h1>
        <p className="text-muted-foreground mt-3 text-lg leading-relaxed max-w-md mx-auto">
          To access your dashboard and DeFi features, please connect your MetaMask wallet first.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row items-center gap-4 w-full max-w-sm">
        <button
          onClick={connect}
          disabled={status === "connecting"}
          className="w-full flex items-center justify-center gap-2 px-6 py-4 rounded-xl bg-primary text-primary-foreground font-bold text-base hover:bg-primary/90 transition-all hover:shadow-lg hover:shadow-primary/20 active:scale-95 disabled:opacity-50"
        >
          <Wallet className="w-5 h-5" />
          {status === "connecting" ? "Connecting..." : "Connect Wallet"}
        </button>
        <button
          onClick={enter}
          className="w-full flex items-center justify-center gap-2 px-6 py-4 rounded-xl border border-border text-foreground font-semibold text-base hover:bg-secondary transition-colors active:scale-95"
        >
          <Eye className="w-5 h-5" />
          Try Demo
        </button>
      </div>

      {status === "error" && (
        <p className="text-sm text-destructive">
          MetaMask is not installed or connection was rejected. Please install MetaMask and try again.
        </p>
      )}

      <div className="w-full max-w-sm glass-card rounded-2xl p-5 text-left">
        <p className="text-xs text-muted-foreground uppercase tracking-wider mb-3">What you'll get access to</p>
        <div className="flex flex-col gap-3">
          {[
            { icon: Zap, label: "AI Trust Score", sub: "View your reputation score" },
            { icon: ShieldCheck, label: "Loan Dashboard", sub: "Request and manage loans" },
            { icon: ArrowRight, label: "Transaction History", sub: "Track all on-chain activity" },
          ].map(({ icon: Icon, label, sub }) => (
            <div key={label} className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <Icon className="w-4 h-4 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">{label}</p>
                <p className="text-xs text-muted-foreground">{sub}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        Or <Link href="/" className="text-primary hover:underline">go back home</Link> to learn more about CreDeFi.
      </p>
    </div>
  )
}
