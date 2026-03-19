"use client"

import { useRef } from "react"
import { Download, Shield, Zap, Wallet, GitBranch, CreditCard } from "lucide-react"
import { useWalletStore } from "@/stores/wallet-store"
import { useDemoStore } from "@/stores/demo-store"

interface CreditPassportProps {
  score: number
  tier: string
  loanLimit: number
  platforms?: number
}

export function CreditPassportCard({ score, tier, loanLimit, platforms = 3 }: CreditPassportProps) {
  const { address } = useWalletStore()
  const { isDemo } = useDemoStore()
  const cardRef = useRef<HTMLDivElement>(null)

  const tierLabel = tier === "low" ? "Excellent" : tier === "medium" ? "Good" : tier === "high" ? "Fair" : "At Risk"
  const tierColor = tier === "low" ? "text-emerald-400" : tier === "medium" ? "text-amber-400" : "text-destructive"

  const r = 52
  const circum = 2 * Math.PI * r
  const pct = Math.min(score / 1000, 1)
  const dash = circum * pct * 0.75

  async function handleDownload() {
    try {
      const html2canvas = (await import("html2canvas")).default
      if (!cardRef.current) return
      const canvas = await html2canvas(cardRef.current, {
        backgroundColor: "#0a0a0a",
        scale: 2,
      })
      const link = document.createElement("a")
      link.download = "credefi-credit-passport.png"
      link.href = canvas.toDataURL()
      link.click()
    } catch {
      // html2canvas not available — gracefully skip
    }
  }

  return (
    <div className="glass-card rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-primary" />
          <h2 className="font-semibold text-foreground">Credit Passport</h2>
        </div>
        <button
          onClick={handleDownload}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          Save
        </button>
      </div>

      <div
        ref={cardRef}
        className="relative overflow-hidden rounded-2xl p-6 border border-primary/20"
        style={{
          background: "linear-gradient(135deg, oklch(0.14 0.02 45 / 0.9), oklch(0.10 0 0 / 0.95))",
        }}
      >
        <div className="absolute top-0 right-0 w-40 h-40 rounded-full bg-primary/5 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-32 h-32 rounded-full bg-primary/3 blur-2xl pointer-events-none" />

        <div className="relative flex items-start justify-between mb-5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Zap className="w-4 h-4 text-primary" />
              <span className="text-sm font-bold text-gradient-orange">CreDeFi</span>
            </div>
            <p className="text-[10px] text-muted-foreground uppercase tracking-widest">Credit Passport</p>
          </div>
          <div className="relative w-20 h-20">
            <svg viewBox="0 0 120 120" className="w-full h-full -rotate-[135deg]">
              <circle cx="60" cy="60" r={r} fill="none" stroke="oklch(0.22 0 0)" strokeWidth="7" strokeLinecap="round"
                strokeDasharray={`${circum * 0.75} ${circum * 0.25}`} />
              <circle cx="60" cy="60" r={r} fill="none" stroke="oklch(0.72 0.19 45)" strokeWidth="7" strokeLinecap="round"
                strokeDasharray={`${dash} ${circum - dash + circum * 0.25}`}
                style={{ filter: "drop-shadow(0 0 6px oklch(0.72 0.19 45 / 0.5))" }} />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-xl font-bold text-foreground">{score}</span>
              <span className="text-[9px] text-muted-foreground">/1000</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-secondary/50">
            <p className="text-[10px] text-muted-foreground">Risk Rating</p>
            <p className={`text-sm font-bold ${tierColor}`}>{tierLabel}</p>
          </div>
          <div className="p-2.5 rounded-xl bg-secondary/50">
            <p className="text-[10px] text-muted-foreground">Loan Limit</p>
            <p className="text-sm font-bold text-foreground">${loanLimit.toLocaleString()}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 mb-3 text-xs text-muted-foreground font-mono">
          <Wallet className="w-3 h-3" />
          {isDemo ? "0x3f4a...9b2c" : address ? `${address.slice(0, 6)}...${address.slice(-4)}` : "Not connected"}
        </div>

        <div className="flex items-center gap-3">
          {[
            { icon: GitBranch, label: "GitHub", active: true },
            { icon: CreditCard, label: "Stripe", active: true },
            { icon: Wallet, label: "Wallet", active: true },
          ].slice(0, platforms).map(({ icon: Icon, label, active }) => (
            <div key={label} className="flex items-center gap-1">
              <div className={`w-5 h-5 rounded flex items-center justify-center ${active ? "bg-primary/20 text-primary" : "bg-secondary text-muted-foreground"}`}>
                <Icon className="w-3 h-3" />
              </div>
              <span className="text-[10px] text-muted-foreground">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
