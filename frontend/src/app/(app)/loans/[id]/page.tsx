"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { CheckCircle, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status-badge";
import { PageShell } from "@/components/layout/page-shell";
import { api } from "@/lib/api-client";

const CONTRACT_TERMS = [
  "Automated liquidation occurs if collateral ratio drops below 120%.",
  "Early repayment is available with 0.5% protocol fee.",
  "Funds are released to the borrower's wallet immediately upon gas confirmation.",
];

export default function LoanDetailPage() {
  const params = useParams();
  const router = useRouter();
  const loanId = params.id as string;
  const [funding, setFunding] = useState(false);

  async function handleFund() {
    setFunding(true);
    try {
      await api.loans.fund({ loan_request_id: loanId });
      router.push("/loans");
    } catch {
      // API may not be connected
    } finally {
      setFunding(false);
    }
  }

  return (
    <PageShell
      title="Loan Contract Preview"
      subtitle="Review the details of your generated smart contract before execution."
      actions={
        <div className="flex items-center gap-2 rounded-full border border-surface-border px-3 py-1 text-xs text-gray-400">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          Network: <span className="font-semibold text-emerald-400">Mainnet</span>
        </div>
      }
    >
      <div className="mx-auto max-w-2xl">
        <Card className="border-l-2 border-l-brand" hover={false}>
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-brand">
                Contract ID
              </p>
              <p className="mt-1 rounded-lg bg-[#0B0F1A] px-3 py-1.5 font-mono text-sm text-gray-300">
                0x74...f48c25
              </p>
            </div>
            <StatusBadge label="Awaiting Confirmation" variant="warning" />
          </div>

          {/* Loan Terms Grid */}
          <div className="mt-8 grid grid-cols-2 gap-y-8">
            <div>
              <p className="text-sm text-gray-500">Loan Principal</p>
              <p className="mt-1">
                <span className="text-3xl font-bold">50,000.00</span>{" "}
                <span className="text-sm text-gray-400">USDC</span>
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Collateral Required</p>
              <p className="mt-1">
                <span className="text-3xl font-bold">32.45</span>{" "}
                <span className="text-sm text-emerald-400">ETH</span>
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Interest Rate (APR)</p>
              <p className="mt-1">
                <span className="text-3xl font-bold text-emerald-400">5.8</span>{" "}
                <span className="text-sm text-gray-400">%</span>
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Repayment Deadline</p>
              <p className="mt-1 text-lg font-bold">
                Dec 15, 2024{" "}
                <span className="text-sm font-normal text-gray-500">
                  (12 Months)
                </span>
              </p>
            </div>
          </div>

          {/* Contract Terms */}
          <div className="mt-8 border-t border-surface-border pt-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400">Contract Terms</h3>
            <ul className="mt-4 space-y-3">
              {CONTRACT_TERMS.map((term) => (
                <li key={term} className="flex items-start gap-2.5 text-sm text-gray-400">
                  <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                  {term}
                </li>
              ))}
            </ul>
          </div>
        </Card>

        {/* Action Buttons */}
        <div className="mt-6 flex gap-4">
          <button
            onClick={() => router.back()}
            className="flex-1 rounded-xl border border-surface-border py-3.5 text-sm font-semibold text-gray-300 transition-all duration-200 hover:bg-surface-light hover:border-gray-600"
          >
            Cancel
          </button>
          <button
            onClick={handleFund}
            disabled={funding}
            className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-brand py-3.5 text-sm font-semibold text-gray-950 transition-all duration-200 hover:bg-amber-400 hover:shadow-lg hover:shadow-brand/20 disabled:opacity-50"
          >
            {funding ? (
              <><Loader2 className="h-4 w-4 animate-spin" /> Processing...</>
            ) : (
              "Accept Contract"
            )}
          </button>
        </div>
      </div>
    </PageShell>
  );
}
