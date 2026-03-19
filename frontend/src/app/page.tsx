"use client";

import Link from "next/link";
import { ArrowRight, Shield, Brain, Landmark, Lock, Globe, Zap } from "lucide-react";
import { Footer } from "@/components/layout/footer";
import { useWalletStore } from "@/stores/wallet-store";

const STEPS = [
  {
    num: "1",
    title: "Connect Your Profiles",
    desc: "Securely link your professional accounts. We use read-only, zero-knowledge proofs to verify your data without censoring it.",
  },
  {
    num: "2",
    title: "Generate Score",
    desc: "Our AI engine analyzes your earnings history, project completions, and client reviews to build your on-chain Credit ID.",
  },
  {
    num: "3",
    title: "Choose Your Limit",
    desc: "Based on your score, you'll be offered a credit limit. High scores unlock lower interest rates and higher verified access.",
  },
  {
    num: "4",
    title: "Instant Borrowing",
    desc: "Draw funds directly to your wallet in USDC or ETH. No paperwork, no banks, no delays.",
  },
  {
    num: "5",
    title: "Grow Your Reputation",
    desc: "Repay on time to boost your score. Your history is recorded on-chain, creating a portable credit profile for the entire DeFi ecosystem.",
  },
];

const FEATURES = [
  {
    icon: Lock,
    title: "ZKP Privacy",
    desc: "Your data remains private. We only verify the facts using zero-knowledge proofs, ensuring your personal information stays encrypted.",
  },
  {
    icon: Zap,
    title: "Dynamic Scoring",
    desc: "Our AI updates your credit score in real-time as you complete jobs and make payments, reflecting your true work reputation.",
  },
  {
    icon: Globe,
    title: "Global Access",
    desc: "Border-free finance. Whether you're in Bali or Berlin, your reputation speaks for itself — no local credit history required.",
  },
];

const PIPELINE = [
  {
    icon: Globe,
    title: "Web2 Source",
    desc: "LinkedIn, GitHub, and gig economy platforms — verified income and track record.",
  },
  {
    icon: Brain,
    title: "AI Analysis",
    desc: "Proprietary LLM models evaluate work quality and trustworthiness.",
  },
  {
    icon: Landmark,
    title: "DeFi Credit",
    desc: "Instant under-collateralised loans based on verified on-chain contracts.",
  },
];

export default function LandingPage() {
  const { connect, status, address } = useWalletStore();

  return (
    <div className="min-h-screen bg-gray-950">
      {/* ── Navbar ─────────────────────────────────────── */}
      <nav className="border-b border-surface-border/50">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-sm font-bold text-gray-950">
                C
              </span>
              <span className="text-lg font-bold">
                Cre<span className="text-brand">DeFi</span>
              </span>
            </Link>
            <div className="hidden gap-6 text-sm text-gray-400 md:flex">
              <Link href="#how" className="hover:text-white transition-colors">How It Works</Link>
              <Link href="#pipeline" className="hover:text-white transition-colors">Reputation</Link>
              <Link href="#features" className="hover:text-white transition-colors">Infrastructure</Link>
            </div>
          </div>
          {address ? (
            <Link
              href="/dashboard"
              className="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-gray-950 hover:bg-amber-400 transition-colors"
            >
              Launch App
            </Link>
          ) : (
            <button
              onClick={connect}
              disabled={status === "connecting"}
              className="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-gray-950 hover:bg-amber-400 transition-colors disabled:opacity-50"
            >
              Connect Wallet
            </button>
          )}
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────── */}
      <section className="mx-auto max-w-7xl px-6 py-20 lg:py-28">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-brand">
              The Future of Credit
            </p>
            <h1 className="mt-4 text-4xl font-extrabold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
              Your Digital Reputation is{" "}
              <span className="text-brand">Your Collateral.</span>
            </h1>
            <p className="mt-6 max-w-lg text-lg leading-relaxed text-gray-400">
              Freelancers and digital nomads are locked out of traditional
              credit. We bridge the gap by turning your verified Web2 work
              history, web3 activity, and AI-driven analytics into DeFi
              borrowing power.
            </p>
            <div className="mt-8 flex gap-4">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-full bg-brand px-6 py-3 text-sm font-semibold text-gray-950 transition-colors hover:bg-amber-400"
              >
                Get Started
              </Link>
              <Link
                href="#how"
                className="inline-flex items-center gap-2 rounded-full border border-surface-border px-6 py-3 text-sm font-semibold text-gray-300 transition-colors hover:bg-surface-light"
              >
                Read Whitepaper
              </Link>
            </div>
          </div>

          {/* Reputation score mockup card */}
          <div className="flex justify-center lg:justify-end">
            <div className="w-72 rounded-2xl border border-surface-border bg-surface p-6">
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                Reputation Score
              </p>
              <p className="mt-3 text-5xl font-extrabold">842</p>
              <p className="text-sm text-emerald-400">GRADE: PLATINUM</p>
              <div className="mt-6 flex items-center justify-between rounded-lg bg-surface-light px-4 py-3">
                <span className="text-sm text-gray-400">Available Credit</span>
                <span className="font-semibold text-white">$12,500.00</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Infrastructure Pipeline ────────────────────── */}
      <section id="pipeline" className="border-t border-surface-border/50 bg-gray-950 py-20">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <h2 className="text-3xl font-bold">Infrastructure Pipeline</h2>
          <p className="mt-2 text-gray-500">
            How we convert your real-world data into financial trust
          </p>
          <div className="mt-12 grid gap-6 sm:grid-cols-3">
            {PIPELINE.map((item, i) => (
              <div
                key={item.title}
                className={`rounded-2xl border p-8 transition-colors ${
                  i === 1
                    ? "border-brand/40 bg-brand/5"
                    : "border-surface-border bg-surface"
                }`}
              >
                <div
                  className={`mx-auto flex h-14 w-14 items-center justify-center rounded-xl ${
                    i === 1
                      ? "bg-brand/20 text-brand"
                      : "bg-surface-light text-gray-400"
                  }`}
                >
                  <item.icon className="h-6 w-6" />
                </div>
                <h3 className="mt-5 text-lg font-semibold">{item.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-500">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 5 Steps ────────────────────────────────────── */}
      <section id="how" className="border-t border-surface-border/50 py-20">
        <div className="mx-auto max-w-7xl px-6">
          <h2 className="text-center text-3xl font-bold">
            5 Steps to Financial Freedom
          </h2>
          <div className="mx-auto mt-12 max-w-2xl space-y-8">
            {STEPS.map((s) => (
              <div key={s.num} className="flex gap-5">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-brand/40 text-sm font-bold text-brand">
                  {s.num}
                </div>
                <div>
                  <h3 className="font-semibold">{s.title}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-gray-500">
                    {s.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Feature Cards ──────────────────────────────── */}
      <section id="features" className="border-t border-surface-border/50 py-20">
        <div className="mx-auto grid max-w-7xl gap-6 px-6 sm:grid-cols-3">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-2xl border border-surface-border bg-surface p-8"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand/15 text-brand">
                <f.icon className="h-6 w-6" />
              </div>
              <h3 className="mt-5 font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-gray-500">
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ────────────────────────────────────────── */}
      <section className="border-t border-surface-border/50 py-20">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <h2 className="text-3xl font-bold sm:text-4xl">
            Stop Waiting for the Bank.
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-gray-500">
            Join 15,000+ freelancers leveraging their work history for DeFi
            liquidity.
          </p>
          <Link
            href="/dashboard"
            className="mt-8 inline-flex items-center gap-2 rounded-full bg-brand px-8 py-3.5 text-sm font-semibold text-gray-950 transition-colors hover:bg-amber-400"
          >
            Launch App <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
}
