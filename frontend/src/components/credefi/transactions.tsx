"use client"

import { useEffect, useState } from "react"
import {
  Download,
  RefreshCw,
  ExternalLink,
  TrendingUp,
  ShieldCheck,
  Clock,
  ArrowUpRight,
  ArrowDownLeft,
} from "lucide-react"
import { api } from "@/lib/api-client"
import { useDemoStore } from "@/stores/demo-store"
import type { LoanRequest } from "@/types"
import { toast } from "sonner"

const TABS = ["All Activities", "Loans", "Repayments", "Lending"]

interface TxRow {
  date: string
  time: string
  type: string
  asset: string
  assetSub: string
  status: "Confirmed" | "Pending" | "Failed"
  txHash: string
  isCredit: boolean
}

function loanToTx(loan: LoanRequest): TxRow {
  const date = new Date(loan.created_at)
  return {
    date: date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
    time: date.toLocaleTimeString("en-US", { hour12: false }) + " UTC",
    type: loan.status === "REPAID" ? "Loan Repayment" : loan.status === "FUNDED" ? "Loan Funded" : "Loan Request",
    asset: `${loan.amount.toLocaleString()} ${loan.currency}`,
    assetSub: `Value: $${loan.amount.toLocaleString()}`,
    status: loan.status === "PENDING" ? "Pending" : loan.status === "DEFAULTED" || loan.status === "CANCELLED" ? "Failed" : "Confirmed",
    txHash: `0x${loan.id.slice(0, 4)}…${loan.id.slice(-4)}`,
    isCredit: loan.status === "FUNDED" || loan.status === "ACTIVE",
  }
}

const FALLBACK_TXS: TxRow[] = [
  {
    date: "Oct 24, 2023", time: "14:32:01 UTC",
    type: "Lending Deposit", asset: "2,500.00 USDC",
    assetSub: "Value: $2,500.00", status: "Confirmed",
    txHash: "0x7f…e3a9", isCredit: false,
  },
  {
    date: "Oct 23, 2023", time: "09:15:44 UTC",
    type: "Loan Request", asset: "0.45 ETH",
    assetSub: "Value: $1,120.40", status: "Pending",
    txHash: "0x9a…b2c1", isCredit: true,
  },
  {
    date: "Oct 22, 2023", time: "22:04:12 UTC",
    type: "Platform Connected", asset: "MetaMask",
    assetSub: "Browser Extension", status: "Confirmed",
    txHash: "0x1d…8f5e", isCredit: false,
  },
  {
    date: "Oct 20, 2023", time: "18:11:59 UTC",
    type: "Repayment", asset: "1,200.00 DAI",
    assetSub: "Value: $1,200.00", status: "Failed",
    txHash: "0x4c…a721", isCredit: false,
  },
]

function statusColor(s: string) {
  if (s === "Confirmed") return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
  if (s === "Pending") return "text-amber-400 bg-amber-500/10 border-amber-500/20"
  return "text-destructive bg-destructive/10 border-destructive/20"
}

export function TransactionsPage() {
  const { isDemo } = useDemoStore()
  const [activeTab, setActiveTab] = useState(TABS[0])
  const [txs, setTxs] = useState<TxRow[]>(FALLBACK_TXS)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const perPage = 10

  async function loadHistory() {
    if (isDemo) {
      toast.info("Demo mode — showing sample transactions")
      return
    }
    setLoading(true)
    try {
      const loans = await api.loans.history()
      if (loans.length > 0) {
        setTxs(loans.map(loanToTx))
      }
    } catch {
      // Fallback data already set
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [])

  const filtered = txs.filter((tx) => {
    if (activeTab === "All Activities") return true
    if (activeTab === "Loans") return tx.type.includes("Loan")
    if (activeTab === "Repayments") return tx.type.includes("Repay")
    if (activeTab === "Lending") return tx.type.includes("Lending") || tx.type.includes("Deposit")
    return true
  })

  const totalPages = Math.max(1, Math.ceil(filtered.length / perPage))
  const paged = filtered.slice((page - 1) * perPage, page * perPage)

  const stats = {
    total: txs.length,
    confirmed: txs.filter(t => t.status === "Confirmed").length,
    pending: txs.filter(t => t.status === "Pending").length,
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Transaction History</h1>
          <p className="text-sm text-muted-foreground mt-0.5">View all on-chain activities and loan events.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadHistory}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-border text-sm font-medium hover:bg-secondary transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-border text-sm font-medium hover:bg-secondary transition-colors">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid sm:grid-cols-3 gap-4 mb-6">
        {[
          { label: "Total Transactions", value: stats.total.toString(), icon: TrendingUp, color: "text-primary" },
          { label: "Confirmed", value: stats.confirmed.toString(), icon: ShieldCheck, color: "text-emerald-400" },
          { label: "Pending", value: stats.pending.toString(), icon: Clock, color: "text-amber-400" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="glass-card rounded-2xl p-5 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="text-lg font-bold text-foreground">{value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 mb-6 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => { setActiveTab(tab); setPage(1) }}
            className={`px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-secondary"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider p-4">Date</th>
                <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider p-4">Type</th>
                <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider p-4">Asset</th>
                <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider p-4">Status</th>
                <th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider p-4">Tx Hash</th>
              </tr>
            </thead>
            <tbody>
              {paged.map((tx, i) => (
                <tr key={i} className="border-b border-border/50 hover:bg-secondary/50 transition-colors">
                  <td className="p-4">
                    <p className="text-sm font-medium text-foreground">{tx.date}</p>
                    <p className="text-xs text-muted-foreground">{tx.time}</p>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <div className={`w-6 h-6 rounded-lg flex items-center justify-center ${tx.isCredit ? "bg-emerald-500/10" : "bg-primary/10"}`}>
                        {tx.isCredit ? <ArrowDownLeft className="w-3 h-3 text-emerald-400" /> : <ArrowUpRight className="w-3 h-3 text-primary" />}
                      </div>
                      <span className="text-sm font-medium text-foreground">{tx.type}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <p className="text-sm font-medium text-foreground">{tx.asset}</p>
                    <p className="text-xs text-muted-foreground">{tx.assetSub}</p>
                  </td>
                  <td className="p-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${statusColor(tx.status)}`}>
                      <span className="w-1.5 h-1.5 rounded-full bg-current" />
                      {tx.status}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-1.5 text-sm text-muted-foreground font-mono">
                      {tx.txHash}
                      <ExternalLink className="w-3 h-3" />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-border">
            <p className="text-xs text-muted-foreground">
              Page {page} of {totalPages} · {filtered.length} results
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 rounded-lg border border-border text-xs font-medium hover:bg-secondary disabled:opacity-50 transition-colors"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="px-3 py-1.5 rounded-lg border border-border text-xs font-medium hover:bg-secondary disabled:opacity-50 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
