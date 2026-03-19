"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Shield, Brain, Landmark, Lock, Globe, Zap, Play } from "lucide-react";
import { Footer } from "@/components/layout/footer";
import { ResponsiveGrid } from "@/components/ui/responsive-grid";
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
    title: "Privacy-First Design",
    desc: "Your raw data never leaves your device. We only store verified scores and attestations — not your personal information.",
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
    desc: "A 10-factor weighted scoring engine evaluates your work quality, income stability, and transaction history using real data.",
  },
  {
    icon: Landmark,
    title: "DeFi Credit",
    desc: "Instant under-collateralised loans based on verified on-chain contracts.",
  },
];

/* Mini circular progress used in the hero card */
function MiniScoreRing({ score, max = 1000 }: { score: number; max?: number }) {
  const pct = score / max;
  const r = 38;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct);
  return (
    <svg width="96" height="96" viewBox="0 0 96 96" className="animate-count-up">
      <circle cx="48" cy="48" r={r} fill="none" stroke="#1e293b" strokeWidth="6" />
      <circle
        cx="48" cy="48" r={r} fill="none"
        stroke="url(#heroGrad)" strokeWidth="6"
        strokeLinecap="round"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        transform="rotate(-90 48 48)"
        className="transition-all duration-1000"
      />
      <defs>
        <linearGradient id="heroGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#22c55e" />
          <stop offset="100%" stopColor="#f97316" />
        </linearGradient>
      </defs>
      <text x="48" y="44" textAnchor="middle" fill="#f1f5f9" fontSize="18" fontWeight="700">{score}</text>
      <text x="48" y="60" textAnchor="middle" fill="#22c55e" fontSize="8" fontWeight="600">PLATINUM</text>
    </svg>
  );
}

export default function LandingPage() {
  const { connect, status, address, enableDemo, demoMode } = useWalletStore();
  const router = useRouter();

  const handleTryDemo = () => {
    enableDemo();
    router.push("/dashboard");
  };

  return (
    <div className="min-h-screen bg-[#0B0F1A]">
      {/* ── Navbar ─────────────────────────────────────── */}
      <nav className="border-b border-white/[0.06]">
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
              <Link href="#how" className="hover:text-white transition-colors duration-200">How It Works</Link>
              <Link href="#pipeline" className="hover:text-white transition-colors duration-200">Reputation</Link>
              <Link href="#features" className="hover:text-white transition-colors duration-200">Infrastructure</Link>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {address || demoMode ? (
              <Link
                href="/dashboard"
                className="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-gray-950 hover:bg-amber-400 transition-all duration-200 hover:shadow-lg hover:shadow-brand/20"
              >
                Launch App
              </Link>
            ) : (
              <>
                <button
                  onClick={connect}
                  disabled={status === "connecting"}
                  className="rounded-full border-2 border-brand px-5 py-2 text-sm font-semibold text-brand hover:bg-brand hover:text-gray-950 transition-all duration-200 disabled:opacity-50"
                >
                  Connect Wallet
                </button>
                <button
                  onClick={handleTryDemo}
                  className="rounded-full border border-white/10 px-5 py-2 text-sm font-medium text-gray-400 hover:text-brand hover:border-brand/30 transition-all duration-200"
                >
                  Try Demo
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        {/* Gradient glows */}
        <div className="pointer-events-none absolute -top-40 left-1/2 h-[600px] w-[900px] -translate-x-1/2 rounded-full bg-brand/[0.07] blur-3xl animate-pulse-glow" />
        <div className="pointer-events-none absolute -top-20 right-0 h-[350px] w-[450px] rounded-full bg-orange-500/[0.05] blur-3xl" />

        <div className="relative mx-auto max-w-7xl px-6 py-24 lg:py-32">
          <ResponsiveGrid sm={2} className="items-center" gap={4}>
            <div className="animate-slide-up">
              <p className="text-sm font-semibold uppercase tracking-widest text-brand">
                The Future of Credit
              </p>
              <h1 className="mt-5 text-4xl font-extrabold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
                Your Digital Reputation is{" "}
                <span className="bg-gradient-to-r from-brand via-amber-400 to-brand bg-clip-text text-transparent">
                  Your Collateral.
                </span>
              </h1>
              <p className="mt-8 max-w-lg text-lg leading-relaxed text-gray-400">
                Freelancers and digital nomads are locked out of traditional
                credit. We bridge the gap by turning your verified Web2 work
                history, web3 activity, and AI-driven analytics into DeFi
                borrowing power.
              </p>
              <div className="mt-10 flex flex-wrap gap-4">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2 rounded-full bg-brand px-7 py-3.5 text-sm font-semibold text-gray-950 transition-all duration-200 hover:bg-amber-400 hover:shadow-lg hover:shadow-brand/25"
                >
                  Get Started <ArrowRight className="h-4 w-4" />
                </Link>
                <button
                  onClick={handleTryDemo}
                  className="inline-flex items-center gap-2 rounded-full border border-brand/30 bg-brand/10 px-7 py-3.5 text-sm font-semibold text-brand transition-all duration-200 hover:bg-brand/20 hover:shadow-lg hover:shadow-brand/10"
                >
                  <Play className="h-4 w-4" />
                  Try Demo
                </button>
                <Link
                  href="#how"
                  className="inline-flex items-center gap-2 rounded-full border border-surface-border px-7 py-3.5 text-sm font-semibold text-gray-300 transition-all duration-200 hover:bg-surface-light hover:border-gray-600"
                >
                  Read Whitepaper
                </Link>
              </div>
            </div>

            {/* Hero Score Card */}
            <div className="flex justify-center lg:justify-end animate-slide-up-delay">
              <div className="w-80 rounded-2xl border border-surface-border bg-surface p-8 shadow-2xl shadow-black/30">
                <p className="text-xs font-semibold uppercase tracking-widest text-gray-500">
                  Reputation Score
                </p>
                <div className="mt-5 flex items-center gap-5">
                  <MiniScoreRing score={842} />
                  <div>
                    <p className="text-3xl font-extrabold">842</p>
                    <p className="text-sm font-semibold text-emerald-400">GRADE: PLATINUM</p>
                  </div>
                </div>
                <div className="mt-6 rounded-xl bg-surface-light px-4 py-3.5">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">Borrow Limit Based on Score</p>
                  <p className="mt-1 text-xl font-bold">$12,500.00 <span className="text-sm font-normal text-gray-500">USDC</span></p>
                </div>
                <div className="mt-4 flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/20 text-[10px] font-bold text-emerald-400">$</span>
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand/20 text-[10px] font-bold text-brand">Ξ</span>
                  <span className="ml-auto text-[10px] text-gray-600">Verified on-chain</span>
                </div>
              </div>
            </div>
          </ResponsiveGrid>
        </div>
      </section>

      {/* ── Infrastructure Pipeline ────────────────────── */}
      <section id="pipeline" className="border-t border-white/[0.06] py-24">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <h2 className="text-3xl font-bold">Infrastructure Pipeline</h2>
          <p className="mt-3 text-gray-500">
            How we convert your real-world data into financial trust
          </p>
          <ResponsiveGrid sm={3} className="mt-14">
            {PIPELINE.map((item, i) => (
              <div
                key={item.title}
                className={`rounded-2xl border p-8 transition-all duration-300 hover:scale-[1.02] hover:-translate-y-1 ${
                  i === 1
                    ? "border-brand/30 bg-brand/[0.04] shadow-lg shadow-brand/5"
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
          </ResponsiveGrid>
        </div>
      </section>

      {/* ── 5 Steps ────────────────────────────────────── */}
      <section id="how" className="border-t border-white/[0.06] py-24">
        <div className="mx-auto max-w-7xl px-6">
          <h2 className="text-center text-3xl font-bold">
            5 Steps to Financial Freedom
          </h2>
          <div className="mx-auto mt-14 max-w-2xl space-y-8">
            {STEPS.map((s, i) => (
              <div key={s.num} className="flex gap-5" style={{ animationDelay: `${i * 0.08}s` }}>
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-brand/30 bg-brand/5 text-sm font-bold text-brand">
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
      <section id="features" className="border-t border-white/[0.06] py-24">
        <ResponsiveGrid sm={3} className="mx-auto max-w-7xl px-6">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-2xl border border-surface-border bg-surface p-8 transition-all duration-300 hover:border-brand/20 hover:scale-[1.02] hover:-translate-y-1"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <f.icon className="h-6 w-6" />
              </div>
              <h3 className="mt-5 text-lg font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-gray-500">
                {f.desc}
              </p>
            </div>
          ))}
        </ResponsiveGrid>
      </section>

      {/* ── CTA ────────────────────────────────────────── */}
      <section className="border-t border-white/[0.06] py-24">
        <div className="mx-auto max-w-7xl px-6 text-center">
          <h2 className="text-3xl font-bold sm:text-4xl">
            Stop Waiting for the Bank.
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-gray-500">
            Join the first generation of freelancers building on-chain credit
            from real work history.
          </p>
          <Link
            href="/dashboard"
            className="mt-10 inline-flex items-center gap-2 rounded-full bg-brand px-8 py-3.5 text-sm font-semibold text-gray-950 transition-all duration-200 hover:bg-amber-400 hover:shadow-lg hover:shadow-brand/25"
          >
            Launch App <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
}
