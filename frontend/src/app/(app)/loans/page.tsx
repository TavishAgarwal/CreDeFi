"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, SlidersHorizontal, TrendingUp, Heart, Award, Download, ShieldCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { StatusBadge } from "@/components/ui/status-badge";
import { ProgressBar } from "@/components/ui/progress-bar";
import { PageShell } from "@/components/layout/page-shell";
import { ResponsiveGrid } from "@/components/ui/responsive-grid";
import { api } from "@/lib/api-client";
import type { LoanRequest } from "@/types";

interface LoanCardData {
  id: string;
  borrowerInitials: string;
  borrowerName: string;
  borrowerBusiness: string;
  riskTier: string;
  trustScore: number;
  roi: number;
  amount: number;
  currency: string;
  duration: number;
  funded: number;
  incomeSources: string[];
}

const DEMO_LOANS: LoanCardData[] = [
  {
    id: "1",
    borrowerInitials: "JD",
    borrowerName: "Julian Dasher",
    borrowerBusiness: "Logistics Enterprise",
    riskTier: "LOW",
    trustScore: 842,
    roi: 12.4,
    amount: 45000,
    currency: "USDC",
    duration: 6,
    funded: 75,
    incomeSources: ["INV", "RE"],
  },
  {
    id: "2",
    borrowerInitials: "AS",
    borrowerName: "Aria Solutions",
    borrowerBusiness: "SaaS Platform",
    riskTier: "MEDIUM",
    trustScore: 715,
    roi: 18.2,
    amount: 120000,
    currency: "USDC",
    duration: 12,
    funded: 15,
    incomeSources: ["SUB"],
  },
  {
    id: "3",
    borrowerInitials: "BT",
    borrowerName: "Bright Tech",
    borrowerBusiness: "Solar Infrastructure",
    riskTier: "LOW",
    trustScore: 910,
    roi: 10.5,
    amount: 250000,
    currency: "USDC",
    duration: 24,
    funded: 92,
    incomeSources: ["GOV", "REV"],
  },
];

const RECENT_TXS = [
  { id: "#TX-99201", borrower: "Julian Dasher", sub: "Logistics Loan", type: "INVESTMENT", amount: "5,000.00 USDC", date: "Oct 24, 2023", status: "Confirmed" },
  { id: "#TX-99188", borrower: "Urban Dev Group", sub: "Real Estate Yield", type: "INTEREST PAYMENT", amount: "+ 412.50 USDC", date: "Oct 22, 2023", status: "Confirmed" },
  { id: "#TX-99042", borrower: "Platform Wallet", sub: "Main Account", type: "DEPOSIT", amount: "10,000.00 USDC", date: "Oct 18, 2023", status: "Confirmed" },
];

const SOURCE_COLORS: Record<string, string> = {
  INV: "bg-emerald-500/15 text-emerald-400",
  RE: "bg-amber-500/15 text-amber-400",
  SUB: "bg-blue-500/15 text-blue-400",
  GOV: "bg-purple-500/15 text-purple-400",
  REV: "bg-amber-500/15 text-amber-400",
};

function riskBadge(tier: string) {
  switch (tier) {
    case "LOW":
      return <StatusBadge label="Low Risk" variant="success" dot={false} />;
    case "MEDIUM":
      return <StatusBadge label="Medium Risk" variant="warning" dot={false} />;
    case "HIGH":
      return <StatusBadge label="High Risk" variant="error" dot={false} />;
    default:
      return <StatusBadge label={tier} variant="neutral" dot={false} />;
  }
}

function initialsColor(tier: string) {
  switch (tier) {
    case "LOW": return "bg-emerald-600";
    case "MEDIUM": return "bg-amber-600";
    case "HIGH": return "bg-red-600";
    default: return "bg-gray-600";
  }
}

function trustBarColor(score: number) {
  if (score >= 800) return "bg-emerald-500";
  if (score >= 600) return "bg-amber-500";
  return "bg-red-500";
}

function typeBadge(type: string) {
  switch (type) {
    case "INVESTMENT":
      return <span className="rounded-md bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase text-emerald-400">{type}</span>;
    case "INTEREST PAYMENT":
      return <span className="rounded-md bg-brand/15 px-2 py-0.5 text-[10px] font-semibold uppercase text-brand">{type}</span>;
    case "DEPOSIT":
      return <span className="rounded-md bg-blue-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase text-blue-400">{type}</span>;
    default:
      return <span className="rounded-md bg-gray-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase text-gray-400">{type}</span>;
  }
}

export default function MarketplacePage() {
  const [search, setSearch] = useState("");
  const [loans, setLoans] = useState<LoanCardData[]>(DEMO_LOANS);

  useEffect(() => {
    api.loans.marketplace().then(() => {}).catch(() => {});
  }, []);

  const filtered = loans.filter(
    (l) =>
      l.borrowerName.toLowerCase().includes(search.toLowerCase()) ||
      l.borrowerBusiness.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <PageShell
      title="Marketplace"
      subtitle="Discover high-yield lending opportunities backed by verified collateral."
      actions={
        <div className="flex items-center gap-3 text-sm text-gray-400">
          <span className="text-xs uppercase tracking-wider text-gray-500">Lender Balance</span>
          <span className="font-bold text-brand text-lg">$142,500.00 USDC</span>
        </div>
      }
    >
      {/* Stats Row */}
      <ResponsiveGrid className="mb-10" sm={3} gap={1}>
        <StatCard label="Active TVL" value="$4.2M" icon={<TrendingUp className="h-5 w-5" />} sub="+12.4%" subColor="text-emerald-400 bg-emerald-500/10" />
        <StatCard label="Average ROI" value="14.2%" icon={<Heart className="h-5 w-5" />} />
        <StatCard label="Loans Funded" value="1,284" icon={<Award className="h-5 w-5" />} />
      </ResponsiveGrid>

      {/* Filters */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-xl font-semibold">Open Loan Opportunities</h2>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              placeholder="Search borrowers..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="rounded-xl border border-surface-border bg-surface py-2.5 pl-9 pr-4 text-sm text-white outline-none placeholder:text-gray-600 focus:border-brand transition-colors"
            />
          </div>
          <button className="flex items-center gap-1.5 rounded-xl border border-surface-border px-4 py-2.5 text-sm text-gray-400 transition-colors hover:text-white hover:border-gray-600">
            <SlidersHorizontal className="h-4 w-4" /> Filters
          </button>
        </div>
      </div>

      {/* Loan Cards Grid */}
      <ResponsiveGrid sm={2} lg={3}>
        {filtered.map((loan) => (
          <Card key={loan.id} className="flex flex-col justify-between group hover:scale-[1.01] hover:shadow-xl hover:shadow-brand/5">
            <div>
              {/* Header: Name + Risk */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold text-white ${initialsColor(loan.riskTier)}`}>
                    {loan.borrowerInitials}
                  </div>
                  <div>
                    <p className="text-sm font-semibold">{loan.borrowerName}</p>
                    <p className="text-xs text-gray-500">{loan.borrowerBusiness}</p>
                  </div>
                </div>
                {riskBadge(loan.riskTier)}
              </div>

              {/* ROI — big and highlighted */}
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-brand">{loan.roi}%</span>
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">ROI</span>
              </div>

              {/* Trust Score + Income Sources */}
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-gray-500">Trust Score</p>
                  <div className="mt-1.5 flex items-center gap-2">
                    <span className="text-sm font-bold">{loan.trustScore}</span>
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-800/60">
                      <div
                        className={`h-full rounded-full ${trustBarColor(loan.trustScore)}`}
                        style={{ width: `${(loan.trustScore / 1000) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-gray-500">Income Sources</p>
                  <div className="mt-1.5 flex gap-1">
                    {loan.incomeSources.map((src) => (
                      <span
                        key={src}
                        className={`rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${SOURCE_COLORS[src] ?? "bg-gray-500/15 text-gray-400"}`}
                      >
                        {src}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Loan Details */}
              <div className="mt-4 space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Loan Amount</span>
                  <span className="font-semibold">${loan.amount.toLocaleString()} {loan.currency}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Duration</span>
                  <span className="font-semibold">{loan.duration} Months</span>
                </div>
              </div>

              {/* Funding Progress */}
              <div className="mt-4">
                <ProgressBar value={loan.funded} color={loan.funded > 80 ? "bg-emerald-500" : "bg-brand"} />
                <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                  <span className="font-medium">{loan.funded}% Funded</span>
                  <span>${((loan.amount * (100 - loan.funded)) / 100).toLocaleString()} remaining</span>
                </div>
              </div>

              {/* Microcopy */}
              <p className="mt-3 flex items-center gap-1 text-[10px] text-gray-500">
                <ShieldCheck className="h-3 w-3 text-emerald-400" />
                Backed by verified income sources
              </p>
            </div>

            <Link
              href={`/loans/${loan.id}`}
              className="mt-5 flex w-full items-center justify-center rounded-xl bg-brand py-3 text-sm font-semibold text-gray-950 transition-all duration-200 hover:bg-amber-400 hover:shadow-lg hover:shadow-brand/20"
            >
              Fund Loan
            </Link>
          </Card>
        ))}
      </ResponsiveGrid>

      {/* Recent Transactions */}
      <Card className="mt-10" padding={false} hover={false}>
        <div className="flex items-center justify-between border-b border-surface-border px-6 py-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400">Recent Transactions</h3>
          <button className="flex items-center gap-1.5 text-sm font-semibold text-brand transition-colors hover:text-amber-400">
            <Download className="h-4 w-4" /> Download CSV
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-surface-border text-xs uppercase tracking-wider text-gray-500">
                <th className="px-6 py-3 font-medium">Transaction ID</th>
                <th className="px-6 py-3 font-medium">Asset / Borrower</th>
                <th className="px-6 py-3 font-medium">Type</th>
                <th className="px-6 py-3 font-medium">Amount</th>
                <th className="px-6 py-3 font-medium">Date</th>
                <th className="px-6 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {RECENT_TXS.map((tx) => (
                <tr key={tx.id} className="border-b border-surface-border/50 transition-colors duration-200 hover:bg-surface-light">
                  <td className="px-6 py-4 font-mono text-gray-400">{tx.id}</td>
                  <td className="px-6 py-4">
                    <p className="font-medium">{tx.borrower}</p>
                    <p className="text-xs text-gray-500">{tx.sub}</p>
                  </td>
                  <td className="px-6 py-4">{typeBadge(tx.type)}</td>
                  <td className="px-6 py-4 font-medium">{tx.amount}</td>
                  <td className="px-6 py-4 text-gray-400">{tx.date}</td>
                  <td className="px-6 py-4">
                    <span className="text-emerald-400">&bull; {tx.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </PageShell>
  );
}
