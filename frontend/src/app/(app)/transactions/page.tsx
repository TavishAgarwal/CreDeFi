"use client";

import { useState } from "react";
import Link from "next/link";
import { Download, RefreshCw, ExternalLink, TrendingUp, ShieldCheck, Clock, Search, ArrowUpRight, ArrowDownLeft, Link2, Repeat } from "lucide-react";
import { Card } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { StatusBadge } from "@/components/ui/status-badge";
import { PageShell } from "@/components/layout/page-shell";
import { ResponsiveGrid } from "@/components/ui/responsive-grid";

const TABS = ["All Activities", "Loans", "Repayments", "Connections", "Lending"];

interface TxRow {
  date: string;
  time: string;
  type: string;
  typeIcon: string;
  asset: string;
  assetSub: string;
  status: "Confirmed" | "Pending" | "Failed";
  txHash: string;
}

const DEMO_TXS: TxRow[] = [
  {
    date: "Oct 24, 2023",
    time: "14:32:01 UTC",
    type: "Lending Deposit",
    typeIcon: "deposit",
    asset: "2,500.00 USDC",
    assetSub: "Value: $2,500.00",
    status: "Confirmed",
    txHash: "0x7f...e3a9",
  },
  {
    date: "Oct 23, 2023",
    time: "09:15:44 UTC",
    type: "Loan Request",
    typeIcon: "loan",
    asset: "0.45 ETH",
    assetSub: "Value: $1,120.40",
    status: "Pending",
    txHash: "0x9a...b2c1",
  },
  {
    date: "Oct 22, 2023",
    time: "22:04:12 UTC",
    type: "Platform Connected",
    typeIcon: "connection",
    asset: "MetaMask",
    assetSub: "Browser Extension",
    status: "Confirmed",
    txHash: "0x1d...8f5e",
  },
  {
    date: "Oct 20, 2023",
    time: "18:11:59 UTC",
    type: "Repayment",
    typeIcon: "repayment",
    asset: "1,200.00 DAI",
    assetSub: "Value: $1,200.00",
    status: "Failed",
    txHash: "0x4c...a721",
  },
];

function statusVariant(s: TxRow["status"]) {
  switch (s) {
    case "Confirmed":
      return "success" as const;
    case "Pending":
      return "warning" as const;
    case "Failed":
      return "error" as const;
  }
}

function typeIconComponent(icon: string) {
  switch (icon) {
    case "deposit":
      return <ArrowDownLeft className="h-4 w-4" />;
    case "loan":
      return <ArrowUpRight className="h-4 w-4" />;
    case "connection":
      return <Link2 className="h-4 w-4" />;
    case "repayment":
      return <Repeat className="h-4 w-4" />;
    default:
      return <ArrowUpRight className="h-4 w-4" />;
  }
}

function typeIconBg(icon: string) {
  switch (icon) {
    case "deposit":
      return "bg-emerald-500/15 text-emerald-400";
    case "loan":
      return "bg-brand/15 text-brand";
    case "connection":
      return "bg-blue-500/15 text-blue-400";
    case "repayment":
      return "bg-red-500/15 text-red-400";
    default:
      return "bg-gray-500/15 text-gray-400";
  }
}

export default function TransactionsPage() {
  const [activeTab, setActiveTab] = useState("All Activities");
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const totalItems = 128;
  const perPage = 10;
  const totalPages = Math.ceil(totalItems / perPage);

  return (
    <PageShell
      title="Transaction History"
      subtitle="View and manage your protocol activities across the DeFi ecosystem."
      actions={
        <>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              placeholder="Search transactions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="rounded-xl border border-surface-border bg-surface py-2.5 pl-9 pr-4 text-sm text-white outline-none placeholder:text-gray-600 focus:border-brand transition-colors"
            />
          </div>
          <button className="flex items-center gap-2 rounded-xl border border-surface-border px-4 py-2.5 text-sm font-medium text-gray-300 transition-all duration-200 hover:bg-surface-light hover:border-gray-600">
            <Download className="h-4 w-4" /> Export CSV
          </button>
          <button className="flex items-center gap-2 rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-gray-950 transition-all duration-200 hover:bg-amber-400 hover:shadow-lg hover:shadow-brand/20">
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
        </>
      }
    >
      {/* Breadcrumb */}
      <div className="mb-6 flex items-center gap-2 text-sm">
        <Link href="/dashboard" className="text-gray-500 transition-colors hover:text-gray-300">
          Dashboard
        </Link>
        <span className="text-gray-600">&rsaquo;</span>
        <span className="font-medium text-brand">Transactions</span>
      </div>

      {/* Tabs */}
      <Card padding={false} hover={false}>
        <div className="flex gap-1 border-b border-surface-border px-6 pt-4">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`rounded-t-lg px-4 py-2.5 text-sm font-medium transition-colors duration-200 ${
                activeTab === tab
                  ? "border-b-2 border-brand text-brand"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              {tab}
              {tab === "All Activities" && (
                <span className="ml-1.5 rounded-full bg-brand/15 px-2 py-0.5 text-xs text-brand">
                  {totalItems}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-surface-border text-xs uppercase tracking-wider text-gray-500">
                <th className="px-6 py-3.5 font-medium">Date / Time</th>
                <th className="px-6 py-3.5 font-medium">Transaction Type</th>
                <th className="px-6 py-3.5 font-medium">Asset / Amount</th>
                <th className="px-6 py-3.5 font-medium">Status</th>
                <th className="px-6 py-3.5 font-medium">TX Hash</th>
                <th className="px-6 py-3.5 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {DEMO_TXS.map((tx, i) => (
                <tr
                  key={i}
                  className="border-b border-surface-border/50 transition-colors duration-200 hover:bg-surface-light/50"
                >
                  <td className="px-6 py-5">
                    <p className="font-medium">{tx.date}</p>
                    <p className="text-xs text-gray-500">{tx.time}</p>
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`flex h-8 w-8 items-center justify-center rounded-lg ${typeIconBg(tx.typeIcon)}`}
                      >
                        {typeIconComponent(tx.typeIcon)}
                      </span>
                      <span className="font-medium">{tx.type}</span>
                    </div>
                  </td>
                  <td className="px-6 py-5">
                    <p className="font-semibold">{tx.asset}</p>
                    <p className="text-xs text-gray-500">{tx.assetSub}</p>
                  </td>
                  <td className="px-6 py-5">
                    <StatusBadge label={tx.status} variant={statusVariant(tx.status)} />
                  </td>
                  <td className="px-6 py-5 font-mono text-sm text-gray-400">
                    {tx.txHash}
                  </td>
                  <td className="px-6 py-5">
                    <button className="text-gray-500 transition-colors duration-200 hover:text-white">
                      <ExternalLink className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between border-t border-surface-border px-6 py-4">
          <p className="text-sm text-gray-500">
            Showing <span className="font-medium text-white">1-{perPage}</span>{" "}
            of <span className="font-medium text-white">{totalItems}</span>{" "}
            transactions
          </p>
          <div className="flex items-center gap-1">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="rounded-lg px-3 py-1.5 text-sm text-gray-400 transition-colors hover:bg-surface-light disabled:opacity-30"
            >
              &lsaquo;
            </button>
            {[1, 2, 3].map((p) => (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-all duration-200 ${
                  page === p
                    ? "bg-brand text-gray-950 shadow-md shadow-brand/20"
                    : "text-gray-400 hover:bg-surface-light"
                }`}
              >
                {p}
              </button>
            ))}
            <span className="px-1 text-gray-600">...</span>
            <button
              onClick={() => setPage(totalPages)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                page === totalPages
                  ? "bg-brand text-gray-950"
                  : "text-gray-400 hover:bg-surface-light"
              }`}
            >
              {totalPages}
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="rounded-lg px-3 py-1.5 text-sm text-gray-400 transition-colors hover:bg-surface-light disabled:opacity-30"
            >
              &rsaquo;
            </button>
          </div>
        </div>
      </Card>

      {/* Summary Stats */}
      <ResponsiveGrid className="mt-10" sm={3} gap={1}>
        <StatCard
          label="Total Volume"
          value="$24,982.50"
          icon={<TrendingUp className="h-5 w-5" />}
        />
        <StatCard
          label="Success Rate"
          value="98.4%"
          icon={<ShieldCheck className="h-5 w-5" />}
        />
        <StatCard
          label="Avg. Confirmation"
          value="~12s"
          icon={<Clock className="h-5 w-5" />}
        />
      </ResponsiveGrid>
    </PageShell>
  );
}
