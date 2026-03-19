"use client"

import { useCallback, useEffect, useState } from "react"
import { Zap, TrendingUp, TrendingDown, BarChart3 } from "lucide-react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts"
import { api, type SimulationResponse } from "@/lib/api-client"
import { useDemoStore } from "@/stores/demo-store"

interface SliderProps {
  label: string
  value: number
  onChange: (v: number) => void
  icon?: string
}

function FeatureSlider({ label, value, onChange, icon }: SliderProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="text-xs font-semibold text-foreground">{Math.round(value * 100)}%</span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        value={Math.round(value * 100)}
        onChange={(e) => onChange(Number(e.target.value) / 100)}
        className="w-full accent-primary h-1.5 rounded-full bg-secondary cursor-pointer"
      />
    </div>
  )
}

const DEMO_RESULT: SimulationResponse = {
  score: 782,
  risk_tier: "low",
  delta: 0,
  feature_impacts: [
    { feature: "repayment_history", value: 0.85, weight: 0.25, contribution: 0.2125, direction: "positive" },
    { feature: "income", value: 0.7, weight: 0.22, contribution: 0.154, direction: "positive" },
    { feature: "platform_score", value: 0.6, weight: 0.20, contribution: 0.12, direction: "positive" },
    { feature: "income_stability", value: 0.75, weight: 0.18, contribution: 0.135, direction: "positive" },
    { feature: "wallet_age", value: 0.5, weight: 0.15, contribution: 0.075, direction: "positive" },
  ],
  loan_limit: 8800,
  raw_weighted: 0.6965,
}

export function ScoreSimulator() {
  const { isDemo } = useDemoStore()
  const [income, setIncome] = useState(0.7)
  const [stability, setStability] = useState(0.75)
  const [walletAge, setWalletAge] = useState(0.5)
  const [platformScore, setPlatformScore] = useState(0.6)
  const [repayment, setRepayment] = useState(0.85)
  const [result, setResult] = useState<SimulationResponse>(DEMO_RESULT)
  const [loading, setLoading] = useState(false)

  const simulate = useCallback(async () => {
    setLoading(true)
    try {
      if (isDemo) {
        const raw = income * 0.22 + stability * 0.18 + walletAge * 0.15 + platformScore * 0.20 + repayment * 0.25
        const noise = (Math.random() - 0.5) * 0.06
        const transformed = 1 / (1 + Math.exp(-6 * (raw + noise - 0.45)))
        const score = Math.round(300 + 700 * transformed)
        const tier = score >= 750 ? "low" : score >= 600 ? "medium" : score >= 450 ? "high" : "critical"
        setResult({
          score,
          risk_tier: tier,
          delta: Math.round(score - 782),
          feature_impacts: [
            { feature: "repayment_history", value: repayment, weight: 0.25, contribution: +(repayment * 0.25).toFixed(4), direction: repayment >= 0.5 ? "positive" : "negative" },
            { feature: "income", value: income, weight: 0.22, contribution: +(income * 0.22).toFixed(4), direction: income >= 0.5 ? "positive" : "negative" },
            { feature: "platform_score", value: platformScore, weight: 0.20, contribution: +(platformScore * 0.20).toFixed(4), direction: platformScore >= 0.5 ? "positive" : "negative" },
            { feature: "income_stability", value: stability, weight: 0.18, contribution: +(stability * 0.18).toFixed(4), direction: stability >= 0.5 ? "positive" : "negative" },
            { feature: "wallet_age", value: walletAge, weight: 0.15, contribution: +(walletAge * 0.15).toFixed(4), direction: walletAge >= 0.5 ? "positive" : "negative" },
          ],
          loan_limit: tier === "low" ? Math.round(10000 * (score - 300) / 700) : tier === "medium" ? Math.round(5000 * (score - 300) / 700) : 0,
          raw_weighted: +raw.toFixed(4),
        })
      } else {
        const res = await api.intelligence.simulateScore({
          income, income_stability: stability, wallet_age: walletAge,
          platform_score: platformScore, repayment_history: repayment,
          baseline_score: 782,
        })
        setResult(res)
      }
    } catch {
      // Keep last result
    } finally {
      setLoading(false)
    }
  }, [income, stability, walletAge, platformScore, repayment, isDemo])

  useEffect(() => {
    const timer = setTimeout(simulate, 150)
    return () => clearTimeout(timer)
  }, [simulate])

  const chartData = result.feature_impacts.map(f => ({
    name: f.feature.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
    value: +(f.contribution * 100).toFixed(1),
    fill: f.direction === "positive" ? "oklch(0.72 0.19 45)" : "oklch(0.55 0.22 25)",
  }))

  return (
    <div className="glass-card rounded-2xl p-6">
      <div className="flex items-center gap-2 mb-5">
        <BarChart3 className="w-5 h-5 text-primary" />
        <h2 className="font-semibold text-foreground">Score Simulator</h2>
        <span className="text-xs text-muted-foreground ml-auto">What-if analysis</span>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="flex flex-col gap-4">
          <FeatureSlider label="Monthly Income" value={income} onChange={setIncome} />
          <FeatureSlider label="Income Stability" value={stability} onChange={setStability} />
          <FeatureSlider label="Wallet Age" value={walletAge} onChange={setWalletAge} />
          <FeatureSlider label="Platform Score" value={platformScore} onChange={setPlatformScore} />
          <FeatureSlider label="Repayment History" value={repayment} onChange={setRepayment} />
        </div>

        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between p-4 rounded-xl bg-secondary">
            <div>
              <p className="text-xs text-muted-foreground">Simulated Score</p>
              <p className="text-3xl font-bold text-foreground">{result.score}</p>
            </div>
            <div className="text-right">
              <div className={`flex items-center gap-1 text-sm font-semibold ${result.delta >= 0 ? "text-emerald-400" : "text-destructive"}`}>
                {result.delta >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                {result.delta >= 0 ? "+" : ""}{result.delta}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">vs baseline</p>
            </div>
          </div>

          <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-secondary text-sm">
            <span className="text-muted-foreground">Risk Tier</span>
            <span className={`font-semibold ${
              result.risk_tier === "low" ? "text-emerald-400" :
              result.risk_tier === "medium" ? "text-amber-400" :
              "text-destructive"
            }`}>{result.risk_tier.charAt(0).toUpperCase() + result.risk_tier.slice(1)}</span>
          </div>
          <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-secondary text-sm">
            <span className="text-muted-foreground">Loan Limit</span>
            <span className="font-semibold text-foreground">${result.loan_limit.toLocaleString()}</span>
          </div>

          <ResponsiveContainer width="100%" height={130}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 0, right: 10 }}>
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: "oklch(0.56 0 0)" }} width={100} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: "oklch(0.12 0 0)", border: "1px solid oklch(0.22 0 0)", borderRadius: "8px", fontSize: 11 }}
                formatter={(v: number) => [`${v.toFixed(1)}%`, "Contribution"]}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
