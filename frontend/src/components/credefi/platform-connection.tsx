"use client"

import { useState } from "react"
import {
  GitBranch,
  DollarSign,
  Wallet,
  CreditCard,
  Check,
  ExternalLink,
  Activity,
  RefreshCw,
} from "lucide-react"
import { useWalletStore } from "@/stores/wallet-store"
import { useDemoStore } from "@/stores/demo-store"
import { toast } from "sonner"

const platformDefs = [
  {
    id: "github",
    name: "GitHub",
    description: "Analyze commit history, repo activity, and open-source contributions.",
    icon: GitBranch,
    iconColor: "text-sky-400",
    bgColor: "bg-sky-500/10",
    borderColor: "border-sky-500/20",
    connected: true,
    metric: "847 commits · 14 repos",
    lastSync: "2 hours ago",
  },
  {
    id: "upwork",
    name: "Upwork",
    description: "Verify freelance earnings, job success score, and client reviews.",
    icon: Activity,
    iconColor: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/20",
    connected: true,
    metric: "$14,200 earned · 98% JSS",
    lastSync: "4 hours ago",
  },
  {
    id: "stripe",
    name: "Stripe",
    description: "Connect payment processing data to verify income consistency.",
    icon: CreditCard,
    iconColor: "text-violet-400",
    bgColor: "bg-violet-500/10",
    borderColor: "border-violet-500/20",
    connected: false,
    metric: null,
    lastSync: null,
  },
  {
    id: "paypal",
    name: "PayPal",
    description: "Include PayPal transaction history as alternative income proof.",
    icon: DollarSign,
    iconColor: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/20",
    connected: false,
    metric: null,
    lastSync: null,
  },
  {
    id: "wallet",
    name: "Crypto Wallet",
    description: "On-chain wallet history, token holdings, and DeFi interactions.",
    icon: Wallet,
    iconColor: "text-primary",
    bgColor: "bg-primary/10",
    borderColor: "border-primary/20",
    connected: false,
    metric: null,
    lastSync: null,
  },
  {
    id: "fiverr",
    name: "Fiverr",
    description: "Add Fiverr freelance data to strengthen your reputation profile.",
    icon: Activity,
    iconColor: "text-green-400",
    bgColor: "bg-green-500/10",
    borderColor: "border-green-500/20",
    connected: false,
    metric: null,
    lastSync: null,
  },
]

export function PlatformConnectionPage() {
  const { address } = useWalletStore()
  const { isDemo } = useDemoStore()

  const [platforms, setPlatforms] = useState(() =>
    platformDefs.map((p) => {
      if (p.id === "wallet" && (address || isDemo)) {
        return {
          ...p,
          connected: true,
          metric: address ? `${address.slice(0, 6)}...${address.slice(-4)} · On-chain` : "2.3 ETH · 12 ERC-20 tokens",
          lastSync: "Just now",
        }
      }
      return p
    })
  )
  const [syncing, setSyncing] = useState<string | null>(null)

  function toggleConnect(id: string) {
    setPlatforms((prev) =>
      prev.map((p) => {
        if (p.id !== id) return p
        const newConnected = !p.connected
        if (newConnected) {
          toast.success(`${p.name} connected successfully`)
        } else {
          toast.info(`${p.name} disconnected`)
        }
        return {
          ...p,
          connected: newConnected,
          metric: newConnected ? p.metric || "Connected" : null,
          lastSync: newConnected ? "Just now" : null,
        }
      })
    )
  }

  function handleSync(id: string) {
    setSyncing(id)
    toast.info("Syncing data...")
    setTimeout(() => {
      setSyncing(null)
      toast.success("Data synced successfully")
    }, 1800)
  }

  const connected = platforms.filter((p) => p.connected)
  const scoreImpact = 650 + connected.length * 40

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Platform Connections</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Connect your income sources to power your AI Trust Score.
        </p>
      </div>

      <div className="glass-card rounded-2xl p-5 flex items-center gap-4 mb-8 border-primary/30">
        <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center shrink-0">
          <Activity className="w-6 h-6 text-primary" />
        </div>
        <div className="flex-1">
          <p className="text-sm text-muted-foreground">Estimated Trust Score with current connections</p>
          <p className="text-2xl font-bold text-foreground">{scoreImpact} <span className="text-sm font-normal text-muted-foreground">/ 1000</span></p>
        </div>
        <div className="hidden sm:flex flex-col items-end gap-1">
          <span className="text-xs text-muted-foreground">{connected.length} of {platforms.length} connected</span>
          <div className="flex gap-1">
            {platforms.map((p) => (
              <div key={p.id} className={`w-3 h-3 rounded-full ${p.connected ? "bg-primary" : "bg-border"}`} />
            ))}
          </div>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {platforms.map((platform) => {
          const { id, name, description, icon: Icon, iconColor, bgColor, borderColor, connected, metric, lastSync } = platform

          return (
            <div
              key={id}
              className={`glass-card rounded-2xl p-6 flex flex-col gap-5 transition-all hover:border-primary/30 ${connected ? "border-glow" : ""}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className={`w-12 h-12 rounded-2xl ${bgColor} border ${borderColor} flex items-center justify-center`}>
                  <Icon className={`w-6 h-6 ${iconColor}`} />
                </div>
                {connected ? (
                  <span className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Connected
                  </span>
                ) : (
                  <span className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-muted border border-border text-muted-foreground text-xs font-medium">
                    Not Connected
                  </span>
                )}
              </div>

              <div>
                <h3 className="font-semibold text-foreground">{name}</h3>
                <p className="text-sm text-muted-foreground mt-1 leading-relaxed">{description}</p>
              </div>

              {connected && metric && (
                <div className="rounded-xl bg-secondary px-3 py-2">
                  <p className="text-xs text-muted-foreground">Verified Data</p>
                  <p className="text-sm font-medium text-foreground mt-0.5">{metric}</p>
                  {lastSync && <p className="text-xs text-muted-foreground mt-0.5">Last synced: {lastSync}</p>}
                </div>
              )}

              <div className="flex items-center gap-2 mt-auto">
                <button
                  onClick={() => toggleConnect(id)}
                  className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all active:scale-95 ${
                    connected
                      ? "bg-secondary text-muted-foreground hover:text-destructive hover:border-destructive/30 border border-border"
                      : "bg-primary text-primary-foreground hover:bg-primary/90"
                  }`}
                >
                  {connected ? (
                    <>
                      <Check className="w-4 h-4" />
                      Disconnect
                    </>
                  ) : (
                    <>
                      <ExternalLink className="w-4 h-4" />
                      Connect
                    </>
                  )}
                </button>
                {connected && (
                  <button
                    onClick={() => handleSync(id)}
                    className="p-2.5 rounded-xl border border-border hover:bg-secondary transition-colors"
                    aria-label="Sync data"
                  >
                    <RefreshCw className={`w-4 h-4 text-muted-foreground ${syncing === id ? "animate-spin" : ""}`} />
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
