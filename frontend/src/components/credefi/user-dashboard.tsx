"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import {
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  GitBranch,
  Wallet,
  CreditCard,
  Plus,
  ArrowUpRight,
  Activity,
  DollarSign,
  Zap,
  AlertCircle,
  RefreshCw,
  Eye,
} from "lucide-react"
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
} from "recharts"
import { api } from "@/lib/api-client"
import { useWalletStore } from "@/stores/wallet-store"
import { useDemoStore } from "@/stores/demo-store"
import type { TrustScoreResult, SybilAnalysis, GraphMetrics } from "@/types"
import { toast } from "sonner"
import { ScoreSimulator } from "@/components/credefi/score-simulator"
import { CreditPassportCard } from "@/components/credefi/credit-passport"

const FALLBACK_INCOME = [
  { month: "Oct", income: 3200 },
  { month: "Nov", income: 4100 },
  { month: "Dec", income: 3800 },
  { month: "Jan", income: 4600 },
  { month: "Feb", income: 5200 },
  { month: "Mar", income: 4900 },
]

function TrustScoreCard({
  score,
  tier,
  loanLimit,
  loading,
  onRecalculate,
}: {
  score: number
  tier: string
  loanLimit: number
  loading: boolean
  onRecalculate: () => void
}) {
  const max = 1000
  const pct = score / max
  const r = 70
  const circum = 2 * Math.PI * r
  const dash = circum * pct * 0.75
  const gap = circum - dash

  const tierLabel =
    tier === "EXCELLENT" ? "Low Risk" :
    tier === "GOOD" ? "Moderate" :
    tier === "FAIR" ? "Fair" : "High Risk"

  const tierColor =
    tier === "EXCELLENT" || tier === "GOOD"
      ? "text-emerald-400 bg-emerald-500/15 border-emerald-500/25"
      : tier === "FAIR"
        ? "text-amber-400 bg-amber-500/15 border-amber-500/25"
        : "text-destructive bg-destructive/15 border-destructive/25"

  return (
    <div className="glass-card rounded-2xl p-6 flex flex-col gap-6 lg:col-span-1">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-foreground">Trust Score</h2>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${tierColor}`}>
            {tierLabel}
          </span>
          <button
            onClick={onRecalculate}
            disabled={loading}
            className="p-1.5 rounded-lg hover:bg-secondary transition-colors"
            title="Recalculate Trust Score"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-muted-foreground ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>
      <div className="flex flex-col items-center gap-4">
        <div className="relative w-44 h-44">
          <svg viewBox="0 0 180 180" className="w-full h-full -rotate-[135deg]">
            <circle cx="90" cy="90" r={r} fill="none" stroke="oklch(0.22 0 0)" strokeWidth="10" strokeLinecap="round"
              strokeDasharray={`${circum * 0.75} ${circum * 0.25}`} />
            <circle cx="90" cy="90" r={r} fill="none" stroke="oklch(0.72 0.19 45)" strokeWidth="10" strokeLinecap="round"
              strokeDasharray={`${dash} ${gap + circum * 0.25}`}
              style={{ filter: "drop-shadow(0 0 8px oklch(0.72 0.19 45 / 0.6))" }} />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-4xl font-bold text-foreground">{score}</span>
            <span className="text-xs text-muted-foreground">/ 1000</span>
          </div>
        </div>
        <div className="w-full grid grid-cols-3 gap-2">
          {[
            { label: "Income", val: score >= 800 ? "A+" : score >= 600 ? "B+" : "C" },
            { label: "History", val: score >= 750 ? "A" : score >= 500 ? "B" : "C" },
            { label: "On-chain", val: score >= 700 ? "B+" : score >= 400 ? "C+" : "D" },
          ].map(({ label, val }) => (
            <div key={label} className="flex flex-col items-center gap-1 p-2 rounded-xl bg-secondary">
              <span className="text-base font-bold text-primary">{val}</span>
              <span className="text-xs text-muted-foreground">{label}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="flex flex-col gap-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Loan Eligibility</span>
          <span className="text-foreground font-medium">${loanLimit.toLocaleString()}</span>
        </div>
        <div className="h-2 rounded-full bg-secondary overflow-hidden">
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${Math.min(100, (loanLimit / 10000) * 100)}%` }}
          />
        </div>
      </div>
    </div>
  )
}

export function UserDashboard() {
  const { address } = useWalletStore()
  const { isDemo } = useDemoStore()
  const [trustScore, setTrustScore] = useState<TrustScoreResult | null>(null)
  const [sybilData, setSybilData] = useState<SybilAnalysis | null>(null)
  const [graphData, setGraphData] = useState<GraphMetrics | null>(null)
  const [loading, setLoading] = useState(false)
  const [incomeData] = useState(FALLBACK_INCOME)

  const score = trustScore?.score ?? 782
  const tier = trustScore?.risk_tier ?? "EXCELLENT"
  const loanLimit = trustScore?.loan_limit ?? 7500

  const radarData = graphData
    ? [
        { subject: "PageRank", score: Math.round(graphData.pagerank * 100) },
        { subject: "Betweenness", score: Math.round(graphData.betweenness * 100) },
        { subject: "Closeness", score: Math.round(graphData.closeness * 100) },
        { subject: "Clustering", score: Math.round(graphData.clustering * 100) },
        { subject: "Reciprocity", score: Math.round(graphData.reciprocity * 100) },
      ]
    : [
        { subject: "Income", score: 88 },
        { subject: "History", score: 75 },
        { subject: "Activity", score: 92 },
        { subject: "Diversity", score: 68 },
        { subject: "On-chain", score: 81 },
      ]

  const txHistory = [
    { id: "0x3f4a…9b2c", type: "Loan Repayment", amount: "-$420", date: "Mar 18, 2026", status: "Confirmed" },
    { id: "0x7c1e…4d8f", type: "Loan Disbursed", amount: "+$2,500", date: "Feb 28, 2026", status: "Confirmed" },
    { id: "0x9b2a…1c5d", type: "Collateral Deposit", amount: "-$800", date: "Feb 28, 2026", status: "Confirmed" },
    { id: "0x1f8b…3e7a", type: "Interest Payment", amount: "-$37.50", date: "Mar 1, 2026", status: "Confirmed" },
  ]

  const platforms = [
    { name: "GitHub", icon: GitBranch, connected: true, metric: "847 commits", color: "text-sky-400" },
    { name: "Upwork", icon: Activity, connected: true, metric: "$14,200 earned", color: "text-emerald-400" },
    { name: "Stripe", icon: CreditCard, connected: true, metric: "98% success rate", color: "text-violet-400" },
    { name: "Wallet", icon: Wallet, connected: true, metric: address ? `${address.slice(0, 6)}...` : "2.3 ETH balance", color: "text-primary" },
  ]

  async function handleCalculate() {
    if (isDemo) {
      toast.info("Demo mode — showing sample data")
      return
    }
    setLoading(true)
    try {
      const [scoreResult, sybilResult, graphResult] = await Promise.allSettled([
        api.trustScore.calculate(),
        api.sybil.analyze(),
        api.graph.compute(),
      ])
      if (scoreResult.status === "fulfilled") {
        setTrustScore(scoreResult.value)
        toast.success(`Trust Score: ${scoreResult.value.score} (${scoreResult.value.risk_tier})`)
      }
      if (sybilResult.status === "fulfilled") setSybilData(sybilResult.value)
      if (graphResult.status === "fulfilled") setGraphData(graphResult.value)
    } catch {
      toast.error("Failed to calculate scores")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    handleCalculate()
  }, [])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {isDemo && (
        <div className="mb-6 flex items-center gap-3 p-4 rounded-2xl glass-card border-amber-500/30">
          <Eye className="w-5 h-5 text-amber-400 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-amber-400">Demo Mode</p>
            <p className="text-xs text-muted-foreground">You&apos;re viewing sample data. Connect your wallet to see your real dashboard.</p>
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Borrower Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {isDemo ? "0x3f4a...9b2c · Demo User" : address ? `${address.slice(0, 6)}...${address.slice(-4)} · Connected via MetaMask` : "Not connected"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/platforms"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-border text-sm font-medium hover:bg-secondary transition-colors"
          >
            <Plus className="w-4 h-4" />
            Connect Platform
          </Link>
          <Link
            href="/loan"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-colors"
          >
            <Zap className="w-4 h-4" />
            Request Loan
          </Link>
        </div>
      </div>

      {/* Sybil detection warning */}
      {sybilData && sybilData.verdict !== "CLEAN" && (
        <div className="mb-6 flex items-center gap-3 p-4 rounded-2xl glass-card border-destructive/30">
          <AlertCircle className="w-5 h-5 text-destructive shrink-0" />
          <div>
            <p className="text-sm font-semibold text-destructive">
              Sybil Risk Detected: {sybilData.verdict}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Sybil score: {sybilData.sybil_score.toFixed(2)} — This may affect your loan eligibility.
              {sybilData.detectors.map(d => ` ${d.name}: ${d.flags.join(", ")}`).join(";")}
            </p>
          </div>
        </div>
      )}

      {/* Stats row */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { label: "Monthly Income", value: "$4,900", change: "+5.8%", up: true, icon: DollarSign },
          { label: "Active Loans", value: "$2,500", change: "1 active", up: true, icon: CreditCard },
          { label: "Total Repaid", value: "$6,420", change: "On time", up: true, icon: ShieldCheck },
          { label: "Collateral Ratio", value: "42%", change: "-8% from avg", up: false, icon: Activity },
        ].map(({ label, value, change, up, icon: Icon }) => (
          <div key={label} className="glass-card rounded-2xl p-5 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
              <Icon className="w-5 h-5 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="text-lg font-bold text-foreground">{value}</p>
            </div>
            <div className={`flex items-center gap-0.5 text-xs font-medium ${up ? "text-emerald-400" : "text-destructive"}`}>
              {up ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
              {change}
            </div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6 mb-6">
        <TrustScoreCard
          score={score}
          tier={tier}
          loanLimit={loanLimit}
          loading={loading}
          onRecalculate={handleCalculate}
        />

        <div className="glass-card rounded-2xl p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-semibold text-foreground">Income Stability</h2>
            <span className="text-xs text-muted-foreground">Last 6 months</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={incomeData}>
              <defs>
                <linearGradient id="incomeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="oklch(0.72 0.19 45)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="oklch(0.72 0.19 45)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: "oklch(0.56 0 0)" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "oklch(0.56 0 0)" }} axisLine={false} tickLine={false}
                tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`} />
              <Tooltip
                contentStyle={{ background: "oklch(0.12 0 0)", border: "1px solid oklch(0.22 0 0)", borderRadius: "10px", fontSize: 12 }}
                labelStyle={{ color: "oklch(0.95 0 0)" }}
                formatter={(v: number) => [`$${v.toLocaleString()}`, "Income"]}
              />
              <Area type="monotone" dataKey="income" stroke="oklch(0.72 0.19 45)" strokeWidth={2} fill="url(#incomeGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-foreground">Connected Platforms</h2>
            <Link href="/platforms" className="text-xs text-primary hover:underline">Manage</Link>
          </div>
          <div className="flex flex-col gap-3">
            {platforms.map(({ name, icon: Icon, connected, metric, color }) => (
              <div key={name} className="flex items-center gap-3 p-3 rounded-xl bg-secondary">
                <div className={`w-8 h-8 rounded-lg bg-background flex items-center justify-center ${color}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground">{name}</p>
                  <p className="text-xs text-muted-foreground">{metric}</p>
                </div>
                <span className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-400" : "bg-muted-foreground"}`} />
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card rounded-2xl p-6">
          <h2 className="font-semibold text-foreground mb-4">
            {graphData ? "Trust Graph Metrics" : "Reputation Breakdown"}
          </h2>
          <ResponsiveContainer width="100%" height={200}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="oklch(0.22 0 0)" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: "oklch(0.56 0 0)" }} />
              <Radar dataKey="score" stroke="oklch(0.72 0.19 45)" fill="oklch(0.72 0.19 45)" fillOpacity={0.25} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-foreground">Transaction History</h2>
            <Link href="/transactions" className="text-xs text-primary hover:underline">
              <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="flex flex-col gap-2">
            {txHistory.map(({ id, type, amount, date }) => (
              <div key={id} className="flex items-center gap-2 p-2.5 rounded-xl hover:bg-secondary transition-colors">
                <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${amount.startsWith("+") ? "bg-emerald-400" : "bg-primary"}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{type}</p>
                  <p className="text-xs text-muted-foreground">{date}</p>
                </div>
                <span className={`text-sm font-semibold ${amount.startsWith("+") ? "text-emerald-400" : "text-foreground"}`}>
                  {amount}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Score Simulator + Credit Passport */}
      <div className="grid lg:grid-cols-3 gap-6 mt-6">
        <div className="lg:col-span-2">
          <ScoreSimulator />
        </div>
        <CreditPassportCard
          score={score}
          tier={tier}
          loanLimit={loanLimit}
          platforms={4}
        />
      </div>
    </div>
  )
}
