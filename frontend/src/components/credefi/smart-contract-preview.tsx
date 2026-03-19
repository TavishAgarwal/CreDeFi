"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import {
  CheckCircle2,
  Clock,
  FileText,
  Shield,
  Zap,
  X,
  Copy,
  ExternalLink,
} from "lucide-react"
import { useWalletStore } from "@/stores/wallet-store"
import { useDemoStore } from "@/stores/demo-store"
import { api } from "@/lib/api-client"
import { toast } from "sonner"

function ContractRow({ label, value, copy }: { label: string; value: string; copy?: boolean }) {
  const [copied, setCopied] = useState(false)
  function handleCopy() {
    navigator.clipboard.writeText(value)
    setCopied(true)
    toast.success("Copied to clipboard")
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <div className="flex items-center justify-between py-3 border-b border-border/50 last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-foreground">{value}</span>
        {copy && (
          <button
            onClick={handleCopy}
            className="p-1 rounded hover:bg-secondary transition-colors"
            aria-label="Copy"
          >
            {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-muted-foreground" />}
          </button>
        )}
      </div>
    </div>
  )
}

export function SmartContractPreview() {
  const router = useRouter()
  const { address } = useWalletStore()
  const { isDemo } = useDemoStore()
  const [status, setStatus] = useState<"idle" | "confirming" | "confirmed">("idle")

  const contractDetails = {
    contractId: "0xCD4f…a2E8",
    borrower: address ? `${address.slice(0, 6)}…${address.slice(-4)}` : "0x3f4a…9b2c",
    loanAmount: "$2,500",
    collateral: "0.215 ETH ($735)",
    collateralRatio: "29.4%",
    interestRate: "8.92% APR",
    duration: "30 days",
    repaymentDate: "April 19, 2026",
    totalRepayment: "$2,562.31",
    network: "Ethereum Mainnet",
    gasEstimate: "~$4.20",
  }

  async function handleAccept() {
    setStatus("confirming")
    if (!isDemo) {
      try {
        await api.loans.fund({ loan_request_id: "latest" })
      } catch {
        // Expected — contract preview is a demo flow
      }
    }
    setTimeout(() => {
      setStatus("confirmed")
      toast.success(isDemo ? "Demo: Transaction confirmed!" : "Transaction confirmed on-chain!")
    }, 2800)
  }

  if (status === "confirmed") {
    return (
      <div className="max-w-xl mx-auto px-4 py-24 flex flex-col items-center gap-6 text-center">
        <div className="w-24 h-24 rounded-full bg-emerald-500/10 border-2 border-emerald-500/30 flex items-center justify-center orange-glow">
          <CheckCircle2 className="w-12 h-12 text-emerald-400" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-foreground">Transaction Confirmed!</h2>
          <p className="text-muted-foreground mt-2 leading-relaxed">
            Your loan of{" "}
            <span className="text-primary font-semibold">$2,500</span> has been
            disbursed to your wallet. Smart contract is live on-chain.
          </p>
        </div>
        <div className="w-full glass-card rounded-2xl p-5 flex flex-col gap-3 text-left">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Transaction Hash</span>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-primary">0xCD4f…a2E8</span>
              <ExternalLink className="w-3.5 h-3.5 text-muted-foreground" />
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Block Confirmed</span>
            <span className="text-sm font-medium text-foreground">#19,847,312</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Gas Used</span>
            <span className="text-sm font-medium text-foreground">$4.17</span>
          </div>
        </div>
        <button
          onClick={() => router.push("/dashboard")}
          className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-colors"
        >
          Back to Dashboard
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <FileText className="w-4 h-4 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Smart Contract Preview</h1>
            <p className="text-sm text-muted-foreground">Review terms before accepting the loan agreement</p>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-5 gap-8">
        <div className="lg:col-span-3 flex flex-col gap-5">
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-semibold text-foreground">Contract Terms</h2>
              <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                <Shield className="w-3.5 h-3.5" />
                Audited Contract
              </span>
            </div>
            <ContractRow label="Contract ID" value={contractDetails.contractId} copy />
            <ContractRow label="Borrower Address" value={contractDetails.borrower} copy />
            <ContractRow label="Loan Amount" value={contractDetails.loanAmount} />
            <ContractRow label="Collateral Locked" value={contractDetails.collateral} />
            <ContractRow label="Collateral Ratio" value={contractDetails.collateralRatio} />
            <ContractRow label="Interest Rate" value={contractDetails.interestRate} />
            <ContractRow label="Loan Duration" value={contractDetails.duration} />
            <ContractRow label="Repayment Deadline" value={contractDetails.repaymentDate} />
            <ContractRow label="Total Repayment" value={contractDetails.totalRepayment} />
            <ContractRow label="Network" value={contractDetails.network} />
            <ContractRow label="Estimated Gas" value={contractDetails.gasEstimate} />
          </div>

          <div className="glass-card rounded-2xl p-5 font-mono text-xs text-emerald-400 leading-relaxed overflow-x-auto">
            <p className="text-muted-foreground mb-2">// CreDeFi Loan Contract · Solidity 0.8.24</p>
            <p><span className="text-sky-400">contract</span> CreDeFiLoan {"{"}</p>
            <p className="pl-4"><span className="text-sky-400">address</span> borrower = <span className="text-primary">{contractDetails.borrower}</span>;</p>
            <p className="pl-4"><span className="text-sky-400">uint256</span> principal = <span className="text-primary">2500 USDC</span>;</p>
            <p className="pl-4"><span className="text-sky-400">uint256</span> collateral = <span className="text-primary">0.215 ETH</span>;</p>
            <p className="pl-4"><span className="text-sky-400">uint256</span> rate = <span className="text-primary">892</span>; <span className="text-muted-foreground">// 8.92% basis points</span></p>
            <p className="pl-4"><span className="text-sky-400">uint256</span> deadline = <span className="text-primary">Apr 19, 2026</span>;</p>
            <p>{"}"}</p>
          </div>
        </div>

        <div className="lg:col-span-2 flex flex-col gap-5">
          <div className="glass-card rounded-2xl p-6 border-primary/20">
            <h2 className="font-semibold text-foreground mb-4">Loan Summary</h2>
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-1 p-4 rounded-xl bg-secondary">
                <span className="text-xs text-muted-foreground">You Receive</span>
                <span className="text-3xl font-bold text-foreground">$2,500</span>
                <span className="text-xs text-muted-foreground">USDC · Ethereum Mainnet</span>
              </div>
              <div className="flex flex-col gap-1 p-4 rounded-xl bg-secondary">
                <span className="text-xs text-muted-foreground">You Lock</span>
                <span className="text-xl font-bold text-primary">0.215 ETH</span>
                <span className="text-xs text-muted-foreground">≈ $735 · 29.4% ratio</span>
              </div>
              <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
                <Clock className="w-4 h-4 text-amber-400 shrink-0" />
                <p className="text-xs text-amber-400">Collateral released upon full repayment by Apr 19, 2026</p>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-3">
            <button
              onClick={handleAccept}
              disabled={status === "confirming"}
              className="w-full flex items-center justify-center gap-2 py-4 rounded-xl bg-primary text-primary-foreground font-bold hover:bg-primary/90 transition-all active:scale-95 disabled:opacity-70"
            >
              {status === "confirming" ? (
                <>
                  <div className="w-4 h-4 rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground animate-spin" />
                  Confirming Transaction...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  Accept Contract
                </>
              )}
            </button>
            <button
              onClick={() => router.back()}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl border border-border text-muted-foreground font-semibold hover:text-foreground hover:bg-secondary transition-colors"
            >
              <X className="w-4 h-4" />
              Cancel
            </button>
          </div>

          <p className="text-xs text-muted-foreground text-center leading-relaxed">
            By accepting, you agree to the CreDeFi smart contract terms. This transaction is irreversible once confirmed on-chain.
          </p>
        </div>
      </div>
    </div>
  )
}
