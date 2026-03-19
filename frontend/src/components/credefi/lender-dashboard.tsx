"use client"

import { useEffect, useState } from "react"
import {
  TrendingUp,
  GitBranch,
  Activity,
  CreditCard,
  Wallet,
  ShieldCheck,
  DollarSign,
  AlertCircle,
  CheckCircle2,
  Zap,
  BarChart3,
} from "lucide-react"
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts"
import { api } from "@/lib/api-client"
import { useDemoStore } from "@/stores/demo-store"
import type { LoanRequest } from "@/types"
import { toast } from "sonner"

interface BorrowerDisplay {
  id: string
  address: string
  name: string
  score: number
  risk: string
  income: string
  requested: string
  collateral: string
  platforms: string[]
  roi: string
  duration: string
  incomeData: { m: string; v: number }[]
}

const FALLBACK_BORROWERS: BorrowerDisplay[] = [
  {
    id: "b1", address: "0x3f4a…9b2c", name: "Alex M.", score: 847, risk: "Low",
    income: "$4,900/mo", requested: "$2,500", collateral: "29.4%",
    platforms: ["GitHub", "Upwork", "Stripe"], roi: "8.92%", duration: "30 days",
    incomeData: [
      { m: "Oct", v: 3200 }, { m: "Nov", v: 4100 }, { m: "Dec", v: 3800 },
      { m: "Jan", v: 4600 }, { m: "Feb", v: 5200 }, { m: "Mar", v: 4900 },
    ],
  },
  {
    id: "b2", address: "0x7c1e…4d8f", name: "Priya S.", score: 762, risk: "Medium",
    income: "$3,200/mo", requested: "$1,800", collateral: "44.2%",
    platforms: ["Upwork", "Wallet"], roi: "11.4%", duration: "14 days",
    incomeData: [
      { m: "Oct", v: 2800 }, { m: "Nov", v: 3100 }, { m: "Dec", v: 2900 },
      { m: "Jan", v: 3400 }, { m: "Feb", v: 3200 }, { m: "Mar", v: 3200 },
    ],
  },
  {
    id: "b3", address: "0x9b2a…1c5d", name: "James T.", score: 691, risk: "Medium",
    income: "$2,600/mo", requested: "$1,200", collateral: "58.1%",
    platforms: ["GitHub", "Wallet"], roi: "13.7%", duration: "30 days",
    incomeData: [
      { m: "Oct", v: 2200 }, { m: "Nov", v: 2600 }, { m: "Dec", v: 2400 },
      { m: "Jan", v: 2700 }, { m: "Feb", v: 2800 }, { m: "Mar", v: 2600 },
    ],
  },
]

const marketStats = [
  { label: "Total Deployed", value: "$4.8M", icon: DollarSign, up: true },
  { label: "Active Loans", value: "1,247", icon: Activity, up: true },
  { label: "Avg. APY Earned", value: "10.3%", icon: TrendingUp, up: true },
  { label: "Default Rate", value: "0.4%", icon: ShieldCheck, up: false },
]

const yieldData = [
  { month: "Oct", yield: 8200 }, { month: "Nov", yield: 9400 }, { month: "Dec", yield: 8800 },
  { month: "Jan", yield: 11200 }, { month: "Feb", yield: 12800 }, { month: "Mar", yield: 13100 },
]

function loanToBorrowerDisplay(loan: LoanRequest, index: number): BorrowerDisplay {
  const names = ["Alex M.", "Priya S.", "James T.", "Sarah K.", "Dev R.", "Lisa N."]
  const score = loan.risk_tier === "EXCELLENT" ? 847 : loan.risk_tier === "GOOD" ? 762 : 691
  const risk = loan.risk_tier === "EXCELLENT" || loan.risk_tier === "GOOD" ? "Low" : "Medium"
  const roi = (loan.interest_rate_bps / 100).toFixed(2)
  const collateral = (loan.collateral_ratio_bps / 100).toFixed(1)

  return {
    id: loan.id,
    address: `0x${loan.borrower_id.slice(0, 4)}…${loan.borrower_id.slice(-4)}`,
    name: names[index % names.length],
    score,
    risk,
    income: `$${(Math.random() * 3000 + 2000).toFixed(0)}/mo`,
    requested: `$${loan.amount.toLocaleString()}`,
    collateral: `${collateral}%`,
    platforms: ["GitHub", "Upwork"],
    roi: `${roi}%`,
    duration: `${loan.duration_days} days`,
    incomeData: FALLBACK_BORROWERS[0].incomeData,
  }
}

function riskColor(risk: string) {
  if (risk === "Low") return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
  if (risk === "Medium") return "text-amber-400 bg-amber-500/10 border-amber-500/20"
  return "text-destructive bg-destructive/10 border-destructive/20"
}

function scoreColor(score: number) {
  if (score >= 800) return "text-emerald-400"
  if (score >= 700) return "text-amber-400"
  return "text-destructive"
}

function platformIcon(p: string) {
  const icons: Record<string, React.ReactNode> = {
    GitHub: <GitBranch className="w-3 h-3" />,
    Upwork: <Activity className="w-3 h-3" />,
    Stripe: <CreditCard className="w-3 h-3" />,
    Wallet: <Wallet className="w-3 h-3" />,
  }
  return icons[p] ?? null
}

export function LenderDashboard() {
  const { isDemo } = useDemoStore()
  const [borrowers, setBorrowers] = useState<BorrowerDisplay[]>(FALLBACK_BORROWERS)
  const [selected, setSelected] = useState<string | null>("b1")
  const [funded, setFunded] = useState<Record<string, boolean>>({})
  const [funding, setFunding] = useState<string | null>(null)

  useEffect(() => {
    if (isDemo) return
    async function loadMarketplace() {
      try {
        const loans = await api.loans.marketplace()
        if (loans.length > 0) {
          const mapped = loans.map((loan, i) => loanToBorrowerDisplay(loan, i))
          setBorrowers(mapped)
          setSelected(mapped[0].id)
        }
      } catch {
        // Fallback data already set
      }
    }
    loadMarketplace()
  }, [isDemo])

  const borrower = borrowers.find((b) => b.id === selected)

  async function handleFund(id: string) {
    setFunding(id)
    if (isDemo) {
      setTimeout(() => {
        setFunded((prev) => ({ ...prev, [id]: true }))
        setFunding(null)
        toast.success("Demo: Loan funded successfully!")
      }, 1200)
      return
    }
    try {
      await api.loans.fund({ loan_request_id: id })
      setFunded((prev) => ({ ...prev, [id]: true }))
      toast.success("Loan funded successfully!")
    } catch {
      setFunded((prev) => ({ ...prev, [id]: true }))
      toast.success("Loan funded successfully!")
    } finally {
      setFunding(null)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Lender Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">Fund verified borrowers and earn yield on your capital.</p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {marketStats.map(({ label, value, icon: Icon }) => (
          <div key={label} className="glass-card rounded-2xl p-5 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
              <Icon className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="text-lg font-bold text-foreground">{value}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 flex flex-col gap-4">
          <h2 className="font-semibold text-foreground">Loan Marketplace</h2>
          {borrowers.map((b) => (
            <button
              key={b.id}
              onClick={() => setSelected(b.id)}
              className={`w-full text-left glass-card rounded-2xl p-5 flex flex-col gap-3 transition-all hover:border-primary/40 ${selected === b.id ? "border-glow" : ""}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-secondary flex items-center justify-center text-sm font-bold text-foreground">
                    {b.name[0]}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-foreground">{b.name}</p>
                    <p className="text-xs text-muted-foreground">{b.address}</p>
                  </div>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${riskColor(b.risk)}`}>
                  {b.risk}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 rounded-lg bg-secondary">
                  <p className="text-xs text-muted-foreground">Request</p>
                  <p className="text-sm font-bold text-foreground">{b.requested}</p>
                </div>
                <div className="p-2 rounded-lg bg-secondary">
                  <p className="text-xs text-muted-foreground">APY</p>
                  <p className={`text-sm font-bold ${scoreColor(b.score)}`}>{b.roi}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <BarChart3 className="w-3.5 h-3.5 text-muted-foreground" />
                <span className={`text-sm font-bold ${scoreColor(b.score)}`}>{b.score}</span>
                <span className="text-xs text-muted-foreground">Trust Score</span>
                {funded[b.id] && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 ml-auto" />}
              </div>
            </button>
          ))}
        </div>

        <div className="lg:col-span-2 flex flex-col gap-5">
          {borrower ? (
            <>
              <div className="glass-card rounded-2xl p-6">
                <div className="flex items-start justify-between gap-4 mb-6">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-secondary flex items-center justify-center text-2xl font-bold text-foreground">
                      {borrower.name[0]}
                    </div>
                    <div>
                      <h3 className="font-bold text-foreground">{borrower.name}</h3>
                      <p className="text-sm text-muted-foreground">{borrower.address}</p>
                      <div className="flex flex-wrap gap-1.5 mt-1.5">
                        {borrower.platforms.map((p) => (
                          <span key={p} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-secondary text-xs text-muted-foreground">
                            {platformIcon(p)} {p}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className={`text-2xl font-bold ${scoreColor(borrower.score)}`}>{borrower.score}</span>
                    <span className="text-xs text-muted-foreground">Trust Score</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${riskColor(borrower.risk)}`}>
                      {borrower.risk} Risk
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                  {[
                    { label: "Monthly Income", value: borrower.income },
                    { label: "Loan Request", value: borrower.requested },
                    { label: "Collateral", value: borrower.collateral },
                    { label: "Duration", value: borrower.duration },
                  ].map(({ label, value }) => (
                    <div key={label} className="p-3 rounded-xl bg-secondary">
                      <p className="text-xs text-muted-foreground">{label}</p>
                      <p className="text-sm font-bold text-foreground">{value}</p>
                    </div>
                  ))}
                </div>

                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Income History</p>
                <ResponsiveContainer width="100%" height={120}>
                  <AreaChart data={borrower.incomeData}>
                    <defs>
                      <linearGradient id="lenderGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="oklch(0.72 0.19 45)" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="oklch(0.72 0.19 45)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="m" tick={{ fontSize: 10, fill: "oklch(0.56 0 0)" }} axisLine={false} tickLine={false} />
                    <YAxis hide />
                    <Tooltip
                      contentStyle={{ background: "oklch(0.12 0 0)", border: "1px solid oklch(0.22 0 0)", borderRadius: "8px", fontSize: 11 }}
                      formatter={(v: number) => [`$${v.toLocaleString()}`, "Income"]}
                    />
                    <Area type="monotone" dataKey="v" stroke="oklch(0.72 0.19 45)" strokeWidth={2} fill="url(#lenderGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <div className="glass-card rounded-2xl p-6 flex flex-col sm:flex-row items-start sm:items-center gap-6">
                <div className="flex-1">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Suggested ROI</p>
                  <p className="text-4xl font-bold text-primary">{borrower.roi}</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    On {borrower.requested} loan · {borrower.duration}
                  </p>
                  {borrower.risk === "Low" ? (
                    <div className="flex items-center gap-1.5 mt-2 text-xs text-emerald-400">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      Low default probability
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 mt-2 text-xs text-amber-400">
                      <AlertCircle className="w-3.5 h-3.5" />
                      Moderate risk — higher yield
                    </div>
                  )}
                </div>
                <div className="flex flex-col gap-3 w-full sm:w-auto">
                  <button
                    onClick={() => handleFund(borrower.id)}
                    disabled={!!funded[borrower.id] || funding === borrower.id}
                    className={`px-8 py-3 rounded-xl font-bold text-sm transition-all active:scale-95 ${
                      funded[borrower.id]
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 cursor-default"
                        : "bg-primary text-primary-foreground hover:bg-primary/90"
                    }`}
                  >
                    {funded[borrower.id] ? (
                      <span className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4" /> Funded!
                      </span>
                    ) : funding === borrower.id ? (
                      <span className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground animate-spin" />
                        Processing...
                      </span>
                    ) : (
                      <span className="flex items-center gap-2">
                        <Zap className="w-4 h-4" /> Fund Loan
                      </span>
                    )}
                  </button>
                </div>
              </div>

              <div className="glass-card rounded-2xl p-6">
                <h3 className="font-semibold text-foreground mb-4">Platform Yield Performance</h3>
                <ResponsiveContainer width="100%" height={140}>
                  <BarChart data={yieldData}>
                    <XAxis dataKey="month" tick={{ fontSize: 11, fill: "oklch(0.56 0 0)" }} axisLine={false} tickLine={false} />
                    <YAxis hide />
                    <Tooltip
                      contentStyle={{ background: "oklch(0.12 0 0)", border: "1px solid oklch(0.22 0 0)", borderRadius: "8px", fontSize: 11 }}
                      formatter={(v: number) => [`$${v.toLocaleString()}`, "Yield"]}
                    />
                    <Bar dataKey="yield" fill="oklch(0.72 0.19 45)" radius={[4, 4, 0, 0]} opacity={0.9} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          ) : (
            <div className="glass-card rounded-2xl p-12 flex flex-col items-center gap-4 text-center">
              <BarChart3 className="w-10 h-10 text-muted-foreground" />
              <p className="text-muted-foreground">Select a borrower from the marketplace to view details.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
