"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Sparkles, AlertTriangle, Loader2, ShieldCheck, Lock } from "lucide-react";
import { Card } from "@/components/ui/card";
import { PageShell } from "@/components/layout/page-shell";
import { ResponsiveGrid } from "@/components/ui/responsive-grid";
import { api } from "@/lib/api-client";
import type { LoanEligibility } from "@/types";

const DURATION_PRESETS = [30, 90, 180, 365];

const BORROW_ASSETS = ["USDC (USD Coin)", "ETH (Ethereum)", "DAI (Dai)"];
const COLLATERAL_ASSETS = ["ETH (Ethereum)", "WBTC (Wrapped Bitcoin)", "USDC (USD Coin)"];

function trustTierLabel(score: number) {
  if (score >= 950) return { label: "Exceptional", color: "text-emerald-300", bg: "bg-emerald-500/15" };
  if (score >= 850) return { label: "Excellent", color: "text-emerald-400", bg: "bg-emerald-500/15" };
  if (score >= 750) return { label: "Good", color: "text-brand", bg: "bg-brand/15" };
  if (score >= 600) return { label: "Fair", color: "text-amber-400", bg: "bg-amber-500/15" };
  if (score >= 450) return { label: "Moderate", color: "text-orange-400", bg: "bg-orange-500/15" };
  return { label: "Ineligible", color: "text-red-400", bg: "bg-red-500/15" };
}

function ratioColor(ratio: number) {
  if (ratio <= 40) return "text-emerald-400";
  if (ratio <= 80) return "text-brand";
  return "text-orange-400";
}

export default function LoanRequestPage() {
  const router = useRouter();
  const [borrowAsset, setBorrowAsset] = useState(BORROW_ASSETS[0]);
  const [collateralAsset, setCollateralAsset] = useState(COLLATERAL_ASSETS[0]);
  const [amount, setAmount] = useState("");
  const [duration, setDuration] = useState(30);
  const [submitting, setSubmitting] = useState(false);

  // Dynamic eligibility state
  const [eligibility, setEligibility] = useState<LoanEligibility | null>(null);
  const [loadingEligibility, setLoadingEligibility] = useState(true);

  // Fallback demo data for when API is not connected
  const demoEligibility: LoanEligibility = {
    trust_score: 785,
    collateral_ratio: 0.60,
    max_borrow_amount: 10_000,
    interest_rate: 0.08,
    eligible: true,
    message: "Your trust score of 785 unlocks a 60% collateral requirement.",
  };

  useEffect(() => {
    api.loans
      .eligibility()
      .then((data) => {
        setEligibility(data);
        setLoadingEligibility(false);
      })
      .catch(() => {
        // Use demo fallback when API unavailable
        setEligibility(demoEligibility);
        setLoadingEligibility(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const elig = eligibility ?? demoEligibility;
  const collateralRatio = (elig.collateral_ratio ?? 1.5) * 100; // to percentage
  const parsedAmount = parseFloat(amount) || 0;
  const estimatedInterestApr = elig.interest_rate * 100;
  const collateralRequired = parsedAmount > 0 ? (parsedAmount * collateralRatio) / 100 : 0;
  const liquidationPrice = parsedAmount > 0 ? (parsedAmount * 1.2) / (collateralRatio / 100) : 0;
  const tier = trustTierLabel(elig.trust_score);

  async function handleSubmit() {
    if (parsedAmount <= 0 || !elig.eligible) return;
    setSubmitting(true);
    try {
      const result = await api.loans.create({
        amount: parsedAmount,
        currency: borrowAsset.split(" ")[0],
        duration_days: duration,
      });
      router.push(`/loans/${result.id}`);
    } catch {
      // API may not be connected
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageShell
      title="Request Smart Loan"
      subtitle="Our AI engine analyzes your trust score to provide personalized collateral requirements and rates."
    >
      <ResponsiveGrid lgTemplate="1fr 360px" gap={2}>
        {/* ── Form ──────────────────────────── */}
        <Card hover={false}>
          {/* Trust Score Collateral Badge */}
          <div className="mb-6 rounded-2xl border border-brand/20 bg-gradient-to-r from-brand/5 via-transparent to-emerald-500/5 p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand/10">
                  <ShieldCheck className="h-6 w-6 text-brand" />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                    Your Collateral Requirement
                  </p>
                  {loadingEligibility ? (
                    <div className="flex items-center gap-2 mt-1">
                      <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
                      <span className="text-sm text-gray-400">Loading...</span>
                    </div>
                  ) : (
                    <p className={`text-2xl font-bold ${ratioColor(collateralRatio)}`}>
                      {collateralRatio.toFixed(0)}%
                    </p>
                  )}
                </div>
              </div>
              {!loadingEligibility && (
                <div className="text-right">
                  <p className="text-xs text-gray-500">Trust Score</p>
                  <p className="text-xl font-bold">{elig.trust_score.toFixed(0)}</p>
                  <span className={`inline-block mt-0.5 rounded-md px-2 py-0.5 text-[10px] font-semibold ${tier.bg} ${tier.color}`}>
                    {tier.label}
                  </span>
                </div>
              )}
            </div>
            {!loadingEligibility && elig.eligible && (
              <p className="mt-3 flex items-center gap-1.5 text-xs text-gray-400">
                <Lock className="h-3 w-3 text-brand" />
                You unlocked this due to your trust score of{" "}
                <span className="font-semibold text-brand">{elig.trust_score.toFixed(0)}</span>
              </p>
            )}
            {!loadingEligibility && !elig.eligible && (
              <p className="mt-3 flex items-center gap-1.5 text-xs text-red-400">
                <AlertTriangle className="h-3 w-3" />
                {elig.message || "Your trust score is too low for loans."}
              </p>
            )}
          </div>

          {/* Section 1: Loan Details */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400">Loan Details</h3>
            <ResponsiveGrid sm={2} className="mt-4">
              {/* Borrow Asset */}
              <div>
                <label className="text-sm font-medium text-gray-400">Borrow Asset</label>
                <select
                  value={borrowAsset}
                  onChange={(e) => setBorrowAsset(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-surface-border bg-[#0B0F1A] px-4 py-3 text-sm text-white outline-none focus:border-brand transition-colors"
                >
                  {BORROW_ASSETS.map((a) => (
                    <option key={a}>{a}</option>
                  ))}
                </select>
              </div>

              {/* Collateral Asset */}
              <div>
                <label className="text-sm font-medium text-gray-400">Collateral Asset</label>
                <select
                  value={collateralAsset}
                  onChange={(e) => setCollateralAsset(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-surface-border bg-[#0B0F1A] px-4 py-3 text-sm text-white outline-none focus:border-brand transition-colors"
                >
                  {COLLATERAL_ASSETS.map((a) => (
                    <option key={a}>{a}</option>
                  ))}
                </select>
              </div>

              {/* Loan Amount */}
              <div>
                <label className="text-sm font-medium text-gray-400">Loan Amount</label>
                <div className="relative mt-1.5">
                  <input
                    type="number"
                    placeholder="0.00"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full rounded-xl border border-surface-border bg-[#0B0F1A] px-4 py-3 pr-16 text-sm text-white outline-none focus:border-brand transition-colors"
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-semibold text-gray-500">
                    {borrowAsset.split(" ")[0]}
                  </span>
                </div>
                <div className="mt-1.5 flex items-center justify-between text-xs text-gray-600">
                  <span>Max: {elig.max_borrow_amount.toLocaleString()} {borrowAsset.split(" ")[0]}</span>
                  <button
                    className="text-brand hover:text-amber-400 transition-colors"
                    onClick={() => setAmount(String(elig.max_borrow_amount))}
                  >
                    Max Amount
                  </button>
                </div>
              </div>

              {/* Duration */}
              <div>
                <label className="text-sm font-medium text-gray-400">Duration</label>
                <div className="relative mt-1.5">
                  <input
                    type="number"
                    value={duration}
                    onChange={(e) => setDuration(Number(e.target.value))}
                    className="w-full rounded-xl border border-surface-border bg-[#0B0F1A] px-4 py-3 pr-16 text-sm text-white outline-none focus:border-brand transition-colors"
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-semibold text-gray-500">
                    Days
                  </span>
                </div>
                <div className="mt-2 flex gap-2">
                  {DURATION_PRESETS.map((d) => (
                    <button
                      key={d}
                      onClick={() => setDuration(d)}
                      className={`rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all duration-200 ${
                        duration === d
                          ? "bg-brand text-gray-950 shadow-md shadow-brand/20"
                          : "bg-surface-light text-gray-400 hover:text-white"
                      }`}
                    >
                      {d}d
                    </button>
                  ))}
                </div>
              </div>
            </ResponsiveGrid>
          </div>

          {/* Section 2: Dynamic Collateral Summary (read-only) */}
          <div className="mt-8 border-t border-surface-border pt-8">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400">Collateral Summary</h3>
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div className="rounded-xl border border-surface-border bg-surface-light p-4">
                <p className="text-xs text-gray-500">Collateral Ratio</p>
                <p className={`mt-1 text-lg font-bold ${ratioColor(collateralRatio)}`}>
                  {collateralRatio.toFixed(0)}%
                </p>
              </div>
              <div className="rounded-xl border border-surface-border bg-surface-light p-4">
                <p className="text-xs text-gray-500">Collateral Required</p>
                <p className="mt-1 text-lg font-bold">
                  {collateralRequired > 0
                    ? `$${collateralRequired.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
                    : "—"}
                  <span className="text-xs font-normal text-gray-400 ml-1">
                    {collateralAsset.split(" ")[0]}
                  </span>
                </p>
              </div>
            </div>
          </div>

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={parsedAmount <= 0 || submitting || !elig.eligible}
            className="mt-8 flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-4 text-sm font-semibold text-gray-950 transition-all duration-200 hover:bg-amber-400 hover:shadow-lg hover:shadow-brand/20 disabled:opacity-50"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Processing...
              </>
            ) : (
              <>
                Initiate Smart Loan <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>

          {/* Estimated Metrics */}
          <div className="mt-6 grid grid-cols-3 gap-4">
            <div className="rounded-xl border border-surface-border bg-surface-light p-4">
              <p className="text-xs text-gray-500">Interest Rate</p>
              <p className="mt-1 text-lg font-bold">
                {estimatedInterestApr.toFixed(1)}% <span className="text-xs font-normal text-emerald-400">APR</span>
              </p>
            </div>
            <div className="rounded-xl border border-surface-border bg-surface-light p-4">
              <p className="text-xs text-gray-500">Liquidation Price</p>
              <p className="mt-1 text-lg font-bold">
                ${liquidationPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}{" "}
                <span className="text-xs font-normal text-gray-400">ETH</span>
              </p>
            </div>
            <div className="rounded-xl border border-surface-border bg-surface-light p-4">
              <p className="text-xs text-gray-500">Protocol Fee</p>
              <p className="mt-1 text-lg font-bold">
                0.05<span className="text-xs font-normal text-gray-400">%</span>
              </p>
            </div>
          </div>
        </Card>

        {/* ── Right sidebar ─────────────────── */}
        <div className="space-y-6">
          {/* What happens if you proceed? */}
          <Card hover={false}>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-brand" />
              <h3 className="text-sm font-semibold">What happens if you proceed?</h3>
            </div>
            <ul className="mt-4 space-y-3 text-sm text-gray-400">
              <li className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand" />
                Your collateral ({collateralAsset.split(" ")[0]}) will be locked in a smart contract
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand" />
                {parsedAmount > 0
                  ? `$${collateralRequired.toLocaleString()} collateral required (${collateralRatio.toFixed(0)}% ratio)`
                  : `Your ${collateralRatio.toFixed(0)}% collateral ratio determines the safety margin`}
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                Funds released instantly upon gas confirmation
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-red-400" />
                Liquidation triggered if collateral value drops below threshold
              </li>
            </ul>
          </Card>

          {/* Trust Score Insight */}
          <Card hover={false}>
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-brand" />
              <h3 className="text-sm font-semibold">Trust Score Benefits</h3>
            </div>

            <div className="mt-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Dynamic Collateral</h4>
              <p className="mt-1 text-sm leading-relaxed text-gray-400">
                Your trust score of{" "}
                <span className="font-semibold text-brand">{elig.trust_score.toFixed(0)}</span>{" "}
                earns you a reduced{" "}
                <span className={`font-semibold ${ratioColor(collateralRatio)}`}>
                  {collateralRatio.toFixed(0)}%
                </span>{" "}
                collateral requirement — lower than the baseline 120%.
              </p>
            </div>

            <div className="mt-5">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                How to unlock better rates
              </h4>
              <ul className="mt-2 space-y-2 text-sm text-gray-400">
                <li className="flex items-start gap-2">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                  Repay loans on time to boost your score
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                  Maintain a consistent transaction history
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                  Score 950+ unlocks just 20% collateral
                </li>
              </ul>
            </div>

            {/* Collateral tier visualization */}
            <div className="mt-5 rounded-xl border border-surface-border bg-surface-light p-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
                Collateral Tiers
              </p>
              <div className="space-y-2">
                {[
                  { range: "950–1000", ratio: "20%", active: elig.trust_score >= 950 },
                  { range: "850–949", ratio: "40%", active: elig.trust_score >= 850 && elig.trust_score < 950 },
                  { range: "750–849", ratio: "60%", active: elig.trust_score >= 750 && elig.trust_score < 850 },
                  { range: "600–749", ratio: "80%", active: elig.trust_score >= 600 && elig.trust_score < 750 },
                  { range: "450–599", ratio: "120%", active: elig.trust_score >= 450 && elig.trust_score < 600 },
                ].map((t) => (
                  <div
                    key={t.range}
                    className={`flex items-center justify-between rounded-lg px-3 py-1.5 text-xs transition-colors ${
                      t.active
                        ? "bg-brand/10 border border-brand/30 text-brand font-semibold"
                        : "text-gray-500"
                    }`}
                  >
                    <span>Score {t.range}</span>
                    <span>{t.ratio}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>

          {/* Market Pulse */}
          <Card hover={false}>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              Market Pulse
            </h3>
            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">ETH Price</span>
                <span className="font-medium">
                  $2,451.20{" "}
                  <span className="text-xs text-emerald-400">+1.2%</span>
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Network Congestion</span>
                <span className="font-medium text-emerald-400">LOW</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Gas Price</span>
                <span className="font-medium">
                  18 <span className="text-xs text-gray-500">Gwei</span>
                </span>
              </div>
            </div>
          </Card>
        </div>
      </ResponsiveGrid>
    </PageShell>
  );
}
