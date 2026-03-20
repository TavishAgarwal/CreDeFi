"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import {
  ArrowRight,
  ChevronDown,
  GitBranch,
  Globe,
  TrendingUp,
  CreditCard,
  ShieldCheck,
  Zap,
  Users,
  BarChart3,
  Lock,
  Wallet,
  Eye,
  Download,
  X,
} from "lucide-react"
import { useWalletStore } from "@/stores/wallet-store"
import { useDemoStore } from "@/stores/demo-store"
import { api } from "@/lib/api-client"
import { isMetaMaskInstalled } from "@/lib/wallet"

function MetaMaskDialog({
  open,
  onClose,
}: {
  open: boolean
  onClose: () => void
}) {
  const { enter: enterDemo } = useDemoStore()
  const router = useRouter()

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      {/* Dialog */}
      <div className="relative w-full max-w-md mx-4 glass-card rounded-2xl border border-primary/20 p-8 animate-in fade-in zoom-in-95 duration-200">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 rounded-lg bg-secondary flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex flex-col items-center text-center gap-5">
          {/* Icon */}
          <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
            <Wallet className="w-8 h-8 text-amber-400" />
          </div>

          <div>
            <h3 className="text-xl font-bold text-foreground mb-2">
              MetaMask Not Detected
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              To connect your wallet, you need the MetaMask browser extension
              installed. You can also explore the full app with demo data.
            </p>
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-3 w-full">
            <a
              href="https://metamask.io/download/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 w-full px-6 py-3 rounded-xl bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-all hover:shadow-lg hover:shadow-primary/20 active:scale-95"
            >
              <Download className="w-4 h-4" />
              Install MetaMask
            </a>
            <button
              onClick={() => {
                enterDemo()
                onClose()
                router.push("/dashboard")
              }}
              className="inline-flex items-center justify-center gap-2 w-full px-6 py-3 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-400 font-semibold hover:bg-amber-500/20 transition-colors"
            >
              <Eye className="w-4 h-4" />
              Try Demo Instead
            </button>
          </div>

          <p className="text-xs text-muted-foreground">
            MetaMask is a free browser extension for managing crypto wallets.
          </p>
        </div>
      </div>
    </div>
  )
}

function HeroSection() {
  const [score, setScore] = useState(0)
  const { connect, status, address } = useWalletStore()
  const { enter: enterDemo, isDemo } = useDemoStore()
  const [healthOk, setHealthOk] = useState<boolean | null>(null)
  const [showMetaMaskDialog, setShowMetaMaskDialog] = useState(false)

  useEffect(() => {
    api.health.check().then(() => setHealthOk(true)).catch(() => setHealthOk(false))
  }, [])

  useEffect(() => {
    const timeout = setTimeout(() => {
      const interval = setInterval(() => {
        setScore((prev) => {
          if (prev >= 847) {
            clearInterval(interval)
            return 847
          }
          return prev + 7
        })
      }, 12)
      return () => clearInterval(interval)
    }, 600)
    return () => clearTimeout(timeout)
  }, [])

  return (
    <section className="relative min-h-screen flex items-center overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />
      <div className="absolute top-1/3 right-1/4 w-96 h-96 rounded-full bg-primary/8 blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/4 w-64 h-64 rounded-full bg-primary/5 blur-3xl pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-32 grid lg:grid-cols-2 gap-16 items-center">
        <div className="flex flex-col gap-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-primary/30 bg-primary/10 text-primary text-sm font-medium w-fit">
            <Zap className="w-3.5 h-3.5" />
            Reputation-Powered DeFi Credit
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight text-balance">
            Your Digital{" "}
            <span className="text-gradient-orange">Reputation</span>{" "}
            is Your Collateral
          </h1>

          <p className="text-muted-foreground text-lg leading-relaxed max-w-xl">
            CreDeFi analyzes your Web2 income data from GitHub, Upwork, and
            payment platforms to generate an AI-powered Trust Score, enabling
            you to access DeFi loans without over-collateralization.
          </p>

          <div className="flex flex-wrap items-center gap-4">
            {address || isDemo ? (
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-all hover:shadow-lg hover:shadow-primary/20 active:scale-95"
              >
                Launch App
                <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <button
                onClick={() => {
                  if (!isMetaMaskInstalled()) {
                    setShowMetaMaskDialog(true)
                  } else {
                    connect()
                  }
                }}
                disabled={status === "connecting"}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-all hover:shadow-lg hover:shadow-primary/20 active:scale-95 disabled:opacity-50"
              >
                <Wallet className="w-4 h-4" />
                {status === "connecting" ? "Connecting..." : "Connect Wallet"}
              </button>
            )}
            {!address && !isDemo && (
              <Link
                href="/dashboard"
                onClick={enterDemo}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-400 font-semibold hover:bg-amber-500/20 transition-colors"
              >
                <Eye className="w-4 h-4" />
                Try Demo
              </Link>
            )}
            <Link
              href="/lender"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl border border-border text-foreground font-semibold hover:bg-secondary transition-colors"
            >
              Lend & Earn
            </Link>
          </div>

          <div className="flex items-center gap-6 pt-2">
            {[
              { label: "Active Borrowers", value: "12,400+" },
              { label: "Loans Issued", value: "$4.8M" },
              { label: "Avg Trust Score", value: "810" },
            ].map(({ label, value }) => (
              <div key={label} className="flex flex-col">
                <span className="text-xl font-bold text-foreground">{value}</span>
                <span className="text-xs text-muted-foreground">{label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-col items-center gap-4">
          <div className="w-full max-w-sm glass-card rounded-2xl p-6 border-glow">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">AI Trust Score</p>
                <p className="text-4xl font-bold text-foreground mt-1">{score}</p>
              </div>
              <div className="relative w-20 h-20">
                <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90">
                  <circle cx="40" cy="40" r="32" fill="none" stroke="oklch(0.22 0 0)" strokeWidth="6" />
                  <circle
                    cx="40" cy="40" r="32" fill="none"
                    stroke="oklch(0.72 0.19 45)"
                    strokeWidth="6"
                    strokeLinecap="round"
                    strokeDasharray={`${(score / 1000) * 201} 201`}
                    className="transition-all duration-300"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xs font-semibold text-primary">{Math.round(score / 10)}%</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span className="text-sm text-emerald-400 font-medium">Low Risk • Loan Eligible</span>
            </div>
          </div>

          <div className="w-full max-w-sm glass-card rounded-2xl p-5">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-4">Web2 → AI → DeFi Pipeline</p>
            <div className="flex flex-col gap-3">
              {[
                { icon: Globe, label: "Web2 Income Data", sub: "GitHub · Upwork · Stripe", color: "text-sky-400" },
                { icon: BarChart3, label: "AI Analysis Engine", sub: "Trust Score Computation", color: "text-primary" },
                { icon: Lock, label: "DeFi Smart Contract", sub: "Loan Deployed On-Chain", color: "text-emerald-400" },
              ].map(({ icon: Icon, label, sub, color }, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-xl bg-secondary flex items-center justify-center ${color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">{label}</p>
                    <p className="text-xs text-muted-foreground">{sub}</p>
                  </div>
                  {i < 2 && (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      <MetaMaskDialog open={showMetaMaskDialog} onClose={() => setShowMetaMaskDialog(false)} />
    </section>
  )
}

function ProblemSection() {
  return (
    <section className="py-24 border-t border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <span className="inline-block px-3 py-1 rounded-full border border-destructive/30 bg-destructive/10 text-destructive text-sm font-medium mb-4">
            The Problem
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold text-balance">
            Freelancers Are Locked Out of Credit
          </h2>
          <p className="mt-4 text-muted-foreground text-lg max-w-2xl mx-auto leading-relaxed">
            1.57 billion freelancers globally lack traditional credit history, yet they generate verifiable income on digital platforms every day.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              icon: CreditCard,
              title: "No Credit Score",
              desc: "Traditional banks require formal employment history and credit records — freelancers have neither.",
            },
            {
              icon: TrendingUp,
              title: "Over-collateralized DeFi",
              desc: "Current DeFi protocols demand 150%+ collateral — defeating the purpose of a loan entirely.",
            },
            {
              icon: Users,
              title: "Untapped Income Proof",
              desc: "GitHub commits, Upwork ratings, Stripe payouts — all ignored by legacy financial systems.",
            },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="glass-card rounded-2xl p-6 flex flex-col gap-4 hover:border-primary/30 transition-colors">
              <div className="w-10 h-10 rounded-xl bg-destructive/10 flex items-center justify-center">
                <Icon className="w-5 h-5 text-destructive" />
              </div>
              <h3 className="font-semibold text-foreground">{title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function HowItWorksSection() {
  const steps = [
    { n: "01", title: "Connect Your Platforms", desc: "Link GitHub, Upwork, Stripe or other income sources to your CreDeFi profile." },
    { n: "02", title: "AI Analyzes Your Data", desc: "Our engine processes income stability, project history, and on-chain activity." },
    { n: "03", title: "Receive Trust Score", desc: "Get an AI-generated reputation score between 0–1000 representing your creditworthiness." },
    { n: "04", title: "Request Loan", desc: "Apply for a DeFi loan with minimal or partial collateral based on your Trust Score." },
    { n: "05", title: "Smart Contract Executes", desc: "Loan terms are encoded in a transparent, auditable smart contract on-chain." },
  ]

  return (
    <section className="py-24 border-t border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <span className="inline-block px-3 py-1 rounded-full border border-primary/30 bg-primary/10 text-primary text-sm font-medium mb-4">
            How It Works
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold text-balance">
            From Reputation to Loan in 5 Steps
          </h2>
        </div>

        <div className="relative">
          <div className="hidden lg:block absolute top-8 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-8">
            {steps.map(({ n, title, desc }) => (
              <div key={n} className="flex flex-col items-center text-center gap-3">
                <div className="relative w-16 h-16 rounded-2xl border border-primary/40 bg-primary/10 flex items-center justify-center orange-glow">
                  <span className="text-primary font-bold text-lg">{n}</span>
                </div>
                <h3 className="font-semibold text-foreground">{title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

function FeaturesSection() {
  const features = [
    { icon: ShieldCheck, title: "AI Trust Scores", desc: "Proprietary reputation scoring powered by multi-source income data analysis." },
    { icon: Lock, title: "On-Chain Contracts", desc: "Fully transparent smart contracts — no hidden terms, no intermediaries." },
    { icon: GitBranch, title: "Multi-Platform Support", desc: "GitHub, Upwork, Stripe, Crypto wallets — all connected in one profile." },
    { icon: BarChart3, title: "Risk-Adjusted Rates", desc: "Interest rates and collateral requirements scale dynamically with your score." },
    { icon: Zap, title: "Fast Approvals", desc: "AI-driven underwriting means loan decisions in minutes, not weeks." },
    { icon: Globe, title: "Permissionless Access", desc: "No KYC barriers. Access DeFi lending from anywhere in the world." },
  ]

  return (
    <section className="py-24 border-t border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <span className="inline-block px-3 py-1 rounded-full border border-primary/30 bg-primary/10 text-primary text-sm font-medium mb-4">
            Features
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold text-balance">
            Built for the New Economy
          </h2>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="glass-card rounded-2xl p-6 flex gap-4 hover:border-primary/30 transition-colors group">
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0 group-hover:bg-primary/20 transition-colors">
                <Icon className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground mb-1">{title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function CtaSection() {
  const { connect, status, address } = useWalletStore()
  const { isDemo, enter: enterDemo } = useDemoStore()
  const [showMetaMaskDialog, setShowMetaMaskDialog] = useState(false)

  return (
    <section className="py-24 border-t border-border">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="glass-card rounded-3xl p-12 relative overflow-hidden border-glow">
          <div className="absolute inset-0 bg-primary/5 pointer-events-none" />
          <div className="relative">
            <h2 className="text-3xl sm:text-5xl font-bold text-balance mb-6">
              Start Building Your{" "}
              <span className="text-gradient-orange">DeFi Credit</span>{" "}
              Profile Today
            </h2>
            <p className="text-muted-foreground text-lg mb-8 max-w-2xl mx-auto">
              Connect your platforms, get your Trust Score, and unlock access to undercollateralized crypto loans.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              {address || isDemo ? (
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-primary text-primary-foreground font-bold text-lg hover:bg-primary/90 transition-all hover:shadow-xl hover:shadow-primary/20 active:scale-95"
                >
                  Launch App
                  <ArrowRight className="w-5 h-5" />
                </Link>
              ) : (
                <>
                  <button
                    onClick={() => {
                      if (!isMetaMaskInstalled()) {
                        setShowMetaMaskDialog(true)
                      } else {
                        connect()
                      }
                    }}
                    disabled={status === "connecting"}
                    className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-primary text-primary-foreground font-bold text-lg hover:bg-primary/90 transition-all hover:shadow-xl hover:shadow-primary/20 active:scale-95 disabled:opacity-50"
                  >
                    Connect Wallet
                    <ArrowRight className="w-5 h-5" />
                  </button>
                  <Link
                    href="/dashboard"
                    onClick={enterDemo}
                    className="inline-flex items-center gap-2 px-8 py-4 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-400 font-bold text-lg hover:bg-amber-500/20 transition-colors"
                  >
                    <Eye className="w-5 h-5" />
                    Try Demo
                  </Link>
                </>
              )}
              <Link
                href="/lender"
                className="inline-flex items-center gap-2 px-8 py-4 rounded-xl border border-border text-foreground font-semibold text-lg hover:bg-secondary transition-colors"
              >
                Explore Loan Market
              </Link>
            </div>
          </div>
        </div>
      </div>
      <MetaMaskDialog open={showMetaMaskDialog} onClose={() => setShowMetaMaskDialog(false)} />
    </section>
  )
}

export function LandingPage() {
  return (
    <main className="overflow-x-hidden">
      <HeroSection />
      <ProblemSection />
      <HowItWorksSection />
      <FeaturesSection />
      <CtaSection />
      <footer className="border-t border-border py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-primary flex items-center justify-center">
              <Zap className="w-3 h-3 text-primary-foreground" />
            </div>
            <span className="font-bold">CreDeFi</span>
          </div>
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} CreDeFi Protocol. Built on Ethereum.
          </p>
        </div>
      </footer>
    </main>
  )
}
