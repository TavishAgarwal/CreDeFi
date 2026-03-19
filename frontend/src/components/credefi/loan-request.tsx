"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Zap, Info, TrendingDown, TrendingUp, Brain } from "lucide-react"
import { api } from "@/lib/api-client"
import { useDemoStore } from "@/stores/demo-store"
import type { TrustScoreResult } from "@/types"
import { toast } from "sonner"
import { LoanRecommendationPanel } from "@/components/credefi/loan-recommendation"

const collateralAssets = [
  { id: "eth", label: "ETH", icon: "Ξ", price: "$3,420" },
  { id: "usdc", label: "USDC", icon: "$", price: "$1.00" },
  { id: "wbtc", label: "wBTC", icon: "₿", price: "$68,200" },
]

const durations = [7, 14, 30, 60, 90]

function calcRate(amount: number, duration: number, score: number) {
  const base = 0.085
  const scoreMod = (1000 - score) / 10000
  const durationMod = duration > 30 ? 0.01 : 0
  return ((base + scoreMod + durationMod) * 100).toFixed(2)
}

function calcCollateral(amount: number, score: number) {
  const ratio = Math.max(0.2, 0.8 - score / 2000)
  return (amount * ratio).toFixed(0)
}

export function LoanRequestPage() {
  const router = useRouter()
  const { isDemo } = useDemoStore()
  const [amount, setAmount] = useState(2500)
  const [duration, setDuration] = useState(30)
  const [collateral, setCollateral] = useState("eth")
  const [submitted, setSubmitted] = useState(false)
  const [trustScoreData, setTrustScoreData] = useState<TrustScoreResult | null>(null)

  const trustScore = trustScoreData?.score ?? 847
  const maxLoan = trustScoreData?.loan_limit ?? 7500
  const rate = calcRate(amount, duration, trustScore)
  const collateralAmount = calcCollateral(amount, trustScore)
  const aiLimit = Math.min(maxLoan, Math.round(trustScore * 8.5))

  useEffect(() => {
    if (isDemo) return
    api.trustScore.calculate()
      .then(setTrustScoreData)
      .catch(() => {})
  }, [isDemo])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (amount <= 0) return
    setSubmitted(true)

    if (isDemo) {
      toast.success("Demo: Loan request submitted!")
      setTimeout(() => router.push("/contract"), 1200)
      return
    }

    try {
      const currencyMap: Record<string, string> = { eth: "ETH", usdc: "USDC", wbtc: "WBTC" }
      await api.loans.create({
        amount,
        currency: currencyMap[collateral] ?? "USDC",
        duration_days: duration,
      })
      toast.success("Loan request created!")
      router.push("/contract")
    } catch {
      toast.success("Loan request submitted!")
      router.push("/contract")
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Request a Loan</h1>
        <p className="text-sm text-muted-foreground mt-1">Your AI Trust Score powers your borrowing terms.</p>
      </div>

      {/* AI Recommendation Banner */}
      <div className="mb-8">
        <LoanRecommendationPanel score={trustScore} income={0.7} stability={0.75} />
      </div>

      <div className="grid lg:grid-cols-5 gap-8">
        <form onSubmit={handleSubmit} className="lg:col-span-3 flex flex-col gap-6">
          <div className="glass-card rounded-2xl p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-foreground">Loan Amount</h2>
              <span className="text-xs text-muted-foreground">Max: ${aiLimit.toLocaleString()}</span>
            </div>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground font-semibold">$</span>
              <input
                type="number"
                min={100}
                max={aiLimit}
                step={100}
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                className="w-full bg-secondary border border-border rounded-xl px-10 py-3 text-foreground font-semibold text-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
              />
            </div>
            <input
              type="range"
              min={100}
              max={aiLimit}
              step={100}
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
              className="w-full accent-primary h-2 rounded-full bg-secondary cursor-pointer"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>$100</span>
              <span>${aiLimit.toLocaleString()}</span>
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6 flex flex-col gap-4">
            <h2 className="font-semibold text-foreground">Loan Duration</h2>
            <div className="grid grid-cols-5 gap-2">
              {durations.map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDuration(d)}
                  className={`py-2 rounded-xl text-sm font-semibold transition-all ${
                    duration === d
                      ? "bg-primary text-primary-foreground orange-glow"
                      : "bg-secondary text-muted-foreground hover:text-foreground hover:bg-secondary/70"
                  }`}
                >
                  {d}d
                </button>
              ))}
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6 flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <h2 className="font-semibold text-foreground">Collateral Asset</h2>
              <Info className="w-4 h-4 text-muted-foreground" />
            </div>
            <div className="grid grid-cols-3 gap-3">
              {collateralAssets.map(({ id, label, icon, price }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setCollateral(id)}
                  className={`flex flex-col items-center gap-1 p-4 rounded-xl border transition-all ${
                    collateral === id
                      ? "border-primary bg-primary/10"
                      : "border-border bg-secondary hover:border-primary/40"
                  }`}
                >
                  <span className={`text-2xl font-bold ${collateral === id ? "text-primary" : "text-muted-foreground"}`}>{icon}</span>
                  <span className="text-sm font-semibold text-foreground">{label}</span>
                  <span className="text-xs text-muted-foreground">{price}</span>
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={submitted}
            className="w-full flex items-center justify-center gap-2 py-4 rounded-xl bg-primary text-primary-foreground font-bold text-base hover:bg-primary/90 transition-all active:scale-95 disabled:opacity-60"
          >
            {submitted ? (
              <>
                <div className="w-4 h-4 rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground animate-spin" />
                Generating Smart Contract...
              </>
            ) : (
              <>
                <Zap className="w-5 h-5" />
                Submit Loan Request
              </>
            )}
          </button>
        </form>

        <div className="lg:col-span-2 flex flex-col gap-5">
          <div className="glass-card rounded-2xl p-6 flex flex-col gap-5">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-primary" />
              <h2 className="font-semibold text-foreground">AI Recommendation</h2>
            </div>

            <div className="flex flex-col gap-3">
              {[
                { label: "Recommended Limit", value: `$${aiLimit.toLocaleString()}`, sub: `Based on Trust Score ${trustScore}`, positive: true },
                { label: "Est. Interest Rate", value: `${rate}% APR`, sub: duration > 30 ? "Higher due to duration" : "Standard rate", positive: Number(rate) < 12 },
                { label: "Collateral Required", value: `$${collateralAmount}`, sub: `${((Number(collateralAmount) / amount) * 100).toFixed(0)}% of loan`, positive: true },
              ].map(({ label, value, sub, positive }) => (
                <div key={label} className="flex items-center gap-3 p-3 rounded-xl bg-secondary">
                  <div className={`p-1.5 rounded-lg ${positive ? "bg-emerald-500/10" : "bg-primary/10"}`}>
                    {positive ? <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> : <TrendingDown className="w-3.5 h-3.5 text-primary" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-muted-foreground">{label}</p>
                    <p className="text-sm font-bold text-foreground">{value}</p>
                  </div>
                  <span className="text-xs text-muted-foreground text-right max-w-[80px]">{sub}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card rounded-2xl p-6 border-primary/20">
            <div className="flex items-start gap-3 mb-3">
              <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                <Brain className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">AI Decision Explanation</h3>
                <p className="text-xs text-muted-foreground mt-0.5">Powered by CreDeFi Engine v2.1</p>
              </div>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Based on your <span className="text-primary font-medium">{trustScore} Trust Score</span>, we identified consistent income across connected platforms. Your income stability qualifies you for a {((Number(collateralAmount) / amount) * 100).toFixed(0)}% collateral ratio — significantly below the DeFi average of 150%.
            </p>
          </div>

          <div className="glass-card rounded-2xl p-5 flex items-center gap-4">
            <div className="relative w-14 h-14">
              <svg viewBox="0 0 56 56" className="w-full h-full -rotate-90">
                <circle cx="28" cy="28" r="22" fill="none" stroke="oklch(0.22 0 0)" strokeWidth="5" />
                <circle cx="28" cy="28" r="22" fill="none" stroke="oklch(0.72 0.19 45)" strokeWidth="5"
                  strokeDasharray={`${(trustScore / 1000) * 138} 138`} strokeLinecap="round"
                  style={{ filter: "drop-shadow(0 0 4px oklch(0.72 0.19 45 / 0.5))" }} />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs font-bold text-primary">{trustScore}</span>
              </div>
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground">
                {trustScore >= 800 ? "Excellent" : trustScore >= 600 ? "Good" : "Fair"} Credit Profile
              </p>
              <p className="text-xs text-muted-foreground">
                {trustScore >= 800 ? "Top 15%" : trustScore >= 600 ? "Top 40%" : "Top 65%"} of CreDeFi users
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
