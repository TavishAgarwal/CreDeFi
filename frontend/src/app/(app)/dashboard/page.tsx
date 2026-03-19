"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  RefreshCw,
  Github,
  Wallet,
  Briefcase,
  CreditCard,
  AlertCircle,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status-badge";
import { TrustScoreRing } from "@/components/charts/trust-score-ring";
import { IncomeChart } from "@/components/charts/income-chart";
import { PageShell } from "@/components/layout/page-shell";
import { api } from "@/lib/api-client";
import type { TrustScoreResult } from "@/types";

// ─── Fallback data (used when API is not connected) ──────────────

const FALLBACK_INCOME = [
  { month: "JAN", confirmed: 3200, projected: 800 },
  { month: "FEB", confirmed: 2800, projected: 1200 },
  { month: "MAR", confirmed: 4100, projected: 600 },
  { month: "APR", confirmed: 3600, projected: 1800 },
  { month: "MAY", confirmed: 5200, projected: 2400 },
  { month: "JUN", confirmed: 4800, projected: 3200 },
];

const PLATFORM_ICONS: Record<string, typeof Github> = {
  github: Github,
  upwork: Briefcase,
  stripe: CreditCard,
  wallet: Wallet,
};

interface ReputationItem {
  label: string;
  value: string;
  color: string;
}

interface ConnectedPlatform {
  icon: typeof Github;
  name: string;
  synced: string;
  status: string;
  metric: string;
  metricSub: string;
  color: string;
}

// ─── Page ────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [trustScore, setTrustScore] = useState<TrustScoreResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiConnected, setApiConnected] = useState(false);

  // Try to load the score on mount
  useEffect(() => {
    handleCalculate();
  }, []);

  const score = trustScore?.score ?? 0;
  const tier = trustScore?.risk_tier ?? "—";

  async function handleCalculate() {
    setLoading(true);
    setError(null);
    try {
      const result = await api.trustScore.calculate();
      setTrustScore(result);
      setApiConnected(true);
    } catch (e: unknown) {
      const msg = (e as { detail?: string }).detail ?? "API not connected";
      setError(msg);
      setApiConnected(false);
    } finally {
      setLoading(false);
    }
  }

  // Build reputation breakdown from trust score factors
  const reputationItems: ReputationItem[] = trustScore
    ? [
        {
          label: "Loan Reliability",
          value: `${Math.round((trustScore.features?.loan_reliability ?? 0) * 100)}%`,
          color: (trustScore.features?.loan_reliability ?? 0) > 0.6
            ? "text-emerald-400"
            : "text-gray-300",
        },
        {
          label: "Income Score",
          value: `${Math.round((trustScore.features?.income ?? 0) * 100)}%`,
          color: (trustScore.features?.income ?? 0) > 0.5
            ? "text-emerald-400"
            : "text-gray-300",
        },
        {
          label: "Graph Reputation",
          value: `${Math.round((trustScore.features?.graph_reputation ?? 0) * 100)}%`,
          color: (trustScore.features?.graph_reputation ?? 0) > 0.4
            ? "text-emerald-400"
            : "text-gray-300",
        },
        {
          label: "Platform Quality",
          value: `${Math.round((trustScore.features?.platform_quality ?? 0) * 100)}%`,
          color: (trustScore.features?.platform_quality ?? 0) > 0.5
            ? "text-emerald-400"
            : "text-gray-300",
        },
      ]
    : [
        { label: "Loan Reliability", value: "—", color: "text-gray-500" },
        { label: "Income Score", value: "—", color: "text-gray-500" },
        { label: "Graph Reputation", value: "—", color: "text-gray-500" },
        { label: "Platform Quality", value: "—", color: "text-gray-500" },
      ];

  const riskBarWidth =
    tier === "low"
      ? "w-1/4"
      : tier === "medium"
        ? "w-1/2"
        : tier === "high"
          ? "w-3/4"
          : "w-full";

  const riskLabel =
    tier === "low"
      ? "Low Risk"
      : tier === "medium"
        ? "Medium Risk"
        : tier === "high"
          ? "High Risk"
          : tier === "critical"
            ? "Critical"
            : "Not Calculated";

  const riskVariant =
    tier === "low" ? "success" : tier === "medium" ? "warning" : "error";

  return (
    <PageShell title="Dashboard">
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        {/* ── Left column ────────────────────────────── */}
        <div className="space-y-6">
          {/* Trust Score */}
          <Card className="flex flex-col items-center text-center">
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              Your Trust Score
            </p>
            <div className="relative mt-4">
              <TrustScoreRing score={score} tier={tier} />
            </div>

            {!apiConnected && !loading && (
              <div className="mt-3 flex items-center gap-1.5 text-xs text-gray-500">
                <AlertCircle className="h-3 w-3" />
                Connect to compute your score
              </div>
            )}

            {error && (
              <p className="mt-2 text-xs text-red-400">{error}</p>
            )}

            <p className="mt-4 text-xs text-gray-500">
              {apiConnected
                ? `Calculated from ${Object.keys(trustScore?.features ?? {}).length} factors`
                : "Connect wallet & compute to get your score"}
            </p>
            <button
              onClick={handleCalculate}
              disabled={loading}
              className="mt-3 flex items-center gap-1.5 text-xs text-brand hover:text-amber-400 transition-colors disabled:opacity-50"
            >
              <RefreshCw
                className={`h-3 w-3 ${loading ? "animate-spin" : ""}`}
              />
              {loading ? "Calculating..." : "Recalculate"}
            </button>
          </Card>

          {/* Reputation Breakdown */}
          <Card>
            <h3 className="font-semibold">Reputation Breakdown</h3>
            <div className="mt-4 space-y-3">
              {reputationItems.map((item) => (
                <div
                  key={item.label}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-gray-400">{item.label}</span>
                  <span className={`font-medium ${item.color}`}>
                    {item.value}
                  </span>
                </div>
              ))}
            </div>

            {/* Penalties section — only shown when data is available */}
            {trustScore && trustScore.penalties && trustScore.penalties.total > 0 && (
              <div className="mt-4 border-t border-surface-border pt-3">
                <p className="text-xs font-semibold uppercase tracking-wider text-red-400 mb-2">
                  Active Penalties
                </p>
                <div className="space-y-1">
                  {trustScore.penalties.circular_tx > 0 && (
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-400">Circular Tx</span>
                      <span className="text-red-400">-{(trustScore.penalties.circular_tx * 100).toFixed(0)}%</span>
                    </div>
                  )}
                  {trustScore.penalties.sybil > 0 && (
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-400">Sybil Risk</span>
                      <span className="text-red-400">-{(trustScore.penalties.sybil * 100).toFixed(0)}%</span>
                    </div>
                  )}
                  {trustScore.penalties.decay > 0 && (
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-400">Inactivity Decay</span>
                      <span className="text-red-400">-{(trustScore.penalties.decay * 100).toFixed(0)}%</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="mt-5 border-t border-surface-border pt-4">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Risk Level</span>
                <StatusBadge
                  label={riskLabel}
                  variant={riskVariant as "success" | "warning" | "error"}
                  dot={false}
                />
              </div>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-gray-800">
                <div
                  className={`h-full rounded-full transition-all ${
                    tier === "low"
                      ? "bg-emerald-500"
                      : tier === "medium"
                        ? "bg-yellow-500"
                        : "bg-red-500"
                  } ${riskBarWidth}`}
                />
              </div>
            </div>

            {/* Loan limit */}
            {trustScore && (
              <div className="mt-4 flex items-center justify-between rounded-lg bg-surface-light px-4 py-3">
                <span className="text-sm text-gray-400">Loan Limit</span>
                <span className="font-semibold text-white">
                  ${trustScore.loan_limit?.toLocaleString() ?? "0"}
                </span>
              </div>
            )}
          </Card>

          {/* CTAs */}
          <Link
            href="/loans/request"
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-4 text-sm font-semibold text-gray-950 transition-colors hover:bg-amber-400"
          >
            Request Instant Loan <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/connections"
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-surface-border py-4 text-sm font-semibold text-gray-300 transition-colors hover:bg-surface-light"
          >
            + Connect New Platform
          </Link>
        </div>

        {/* ── Right column ───────────────────────────── */}
        <div className="space-y-6">
          {/* Income Chart */}
          <Card>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                Monthly Income Stream
              </h3>
            </div>
            <IncomeChart data={FALLBACK_INCOME} />
          </Card>

          {/* Connected Platforms */}
          <Card>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-semibold">Connected Platforms</h3>
              <span className="text-xs text-gray-500">
                {trustScore?.connected_accounts ?? 0} Active Sources
              </span>
            </div>

            {!apiConnected ? (
              <div className="py-8 text-center">
                <p className="text-sm text-gray-500">
                  Connect your wallet and compute your trust score to see linked platforms.
                </p>
                <button
                  onClick={handleCalculate}
                  className="mt-3 text-xs font-semibold text-brand hover:text-amber-400 transition-colors"
                >
                  Compute Score
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Show placeholder data matching what the API returns */}
                {[
                  {
                    icon: Wallet,
                    name: "On-chain Wallet",
                    synced: "Real-time",
                    status: "Connected",
                    metric: `Score: ${score}`,
                    metricSub: "TRUST PROOF",
                    color: "bg-amber-800",
                  },
                ].map((p) => (
                  <div
                    key={p.name}
                    className="flex items-center justify-between rounded-lg border border-surface-border bg-surface-light p-4"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`flex h-10 w-10 items-center justify-center rounded-lg ${p.color}`}
                      >
                        <p.icon className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">{p.name}</p>
                        <p className="text-xs text-gray-500">
                          Synced: {p.synced} &middot;{" "}
                          <span className="text-emerald-400">{p.status}</span>
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold">{p.metric}</p>
                      <p className="text-[10px] uppercase tracking-wider text-gray-500">
                        {p.metricSub}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <Link
              href="/connections"
              className="mt-4 block w-full text-center text-xs font-semibold uppercase tracking-wider text-brand hover:text-amber-400 transition-colors"
            >
              + Connect More Platforms
            </Link>
          </Card>
        </div>
      </div>
    </PageShell>
  );
}
