"use client"

import { useEffect, useState } from "react"
import { Brain, ShieldCheck, AlertCircle, TrendingUp, DollarSign, Clock } from "lucide-react"
import { api, type LoanRecommendation } from "@/lib/api-client"
import { useDemoStore } from "@/stores/demo-store"

interface LoanRecommendationPanelProps {
  score: number
  income: number
  stability: number
}

const DEMO_RECOMMENDATION: LoanRecommendation = {
  recommended_amount: 7200,
  recommended_interest: 6.5,
  risk_level: "low",
  reasoning: "Your trust score of 847 qualifies you for our best rates. Strong income supports a higher loan amount. Consistent payment patterns earned you a lower interest rate. No collateral required at this trust level.",
  collateral_ratio: 0,
  max_term_days: 365,
  monthly_payment: 620.5,
  confidence: "high",
}

export function LoanRecommendationPanel({ score, income, stability }: LoanRecommendationPanelProps) {
  const { isDemo } = useDemoStore()
  const [rec, setRec] = useState<LoanRecommendation>(DEMO_RECOMMENDATION)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    async function fetch() {
      setLoading(true)
      try {
        if (isDemo) {
          await new Promise(r => setTimeout(r, 400))
          const baseAmount = score >= 750 ? 10000 : score >= 600 ? 5000 : 1500
          const incomeMult = 0.5 + income * 1.0
          const amount = Math.round(baseAmount * incomeMult / 100) * 100
          const rate = score >= 750 ? 5 + (1 - stability) * 5 : score >= 600 ? 12 + (1 - stability) * 5 : 24
          setRec({
            recommended_amount: amount,
            recommended_interest: +rate.toFixed(2),
            risk_level: score >= 750 ? "low" : score >= 600 ? "medium" : "high",
            reasoning: score >= 750
              ? `Your trust score of ${score} qualifies you for our best rates. ${income >= 0.7 ? "Strong income supports a higher loan amount." : "Consider increasing income for better terms."} ${stability >= 0.7 ? "Consistent payments earned a lower rate." : "Improve payment consistency for better rates."}`
              : `Your trust score of ${score} places you in the ${score >= 600 ? "standard" : "limited"} lending tier. ${stability < 0.5 ? "Low stability increases your interest rate." : ""}`,
            collateral_ratio: score >= 750 ? 0 : score >= 600 ? 0.5 : 1.2,
            max_term_days: score >= 750 ? 365 : score >= 600 ? 180 : 90,
            monthly_payment: +(amount / 12).toFixed(2),
            confidence: score >= 700 && income >= 0.5 ? "high" : "medium",
          })
        } else {
          const data = await api.intelligence.loanRecommend({ score, income, stability })
          setRec(data)
        }
      } catch {
        // keep demo data
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [score, income, stability, isDemo])

  const confidenceColor = rec.confidence === "high" ? "text-emerald-400" : rec.confidence === "medium" ? "text-amber-400" : "text-destructive"

  return (
    <div className="glass-card rounded-2xl p-6">
      <div className="flex items-center gap-2 mb-5">
        <Brain className="w-5 h-5 text-primary" />
        <h2 className="font-semibold text-foreground">AI Loan Recommendation</h2>
        <span className={`ml-auto px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${confidenceColor} bg-current/10 border border-current/20`}>
          {rec.confidence} confidence
        </span>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8 gap-2 text-muted-foreground">
          <div className="w-4 h-4 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
          Analyzing your profile...
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
            {[
              { icon: DollarSign, label: "Recommended", value: `$${rec.recommended_amount.toLocaleString()}`, sub: "Loan Amount" },
              { icon: TrendingUp, label: "Interest Rate", value: `${rec.recommended_interest}%`, sub: "APR" },
              { icon: ShieldCheck, label: "Collateral", value: rec.collateral_ratio === 0 ? "None" : `${(rec.collateral_ratio * 100).toFixed(0)}%`, sub: "Required" },
              { icon: Clock, label: "Max Term", value: `${rec.max_term_days}d`, sub: `~$${rec.monthly_payment.toLocaleString()}/mo` },
            ].map(({ icon: Icon, label, value, sub }) => (
              <div key={label} className="p-3 rounded-xl bg-secondary text-center">
                <Icon className="w-4 h-4 text-primary mx-auto mb-1" />
                <p className="text-lg font-bold text-foreground">{value}</p>
                <p className="text-[10px] text-muted-foreground">{sub}</p>
              </div>
            ))}
          </div>

          <div className="p-4 rounded-xl bg-primary/5 border border-primary/15">
            <div className="flex items-start gap-2">
              <Brain className="w-4 h-4 text-primary mt-0.5 shrink-0" />
              <p className="text-sm text-muted-foreground leading-relaxed">{rec.reasoning}</p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
