"use client"

import { useEffect, useState, useCallback } from "react"
import { AlertTriangle, Network, Shield, Eye } from "lucide-react"
import { useDemoStore } from "@/stores/demo-store"
import { api, type GraphVisualization, type GraphNode, type SuspiciousCluster } from "@/lib/api-client"

const DEMO_GRAPH: GraphVisualization = {
  nodes: [
    { id: "user_main", label: "You", score: 847, risk: "low", is_suspicious: false, cluster_id: null },
    { id: "user_alex", label: "Alex M.", score: 762, risk: "low", is_suspicious: false, cluster_id: null },
    { id: "user_priya", label: "Priya S.", score: 691, risk: "medium", is_suspicious: false, cluster_id: null },
    { id: "user_james", label: "James T.", score: 823, risk: "low", is_suspicious: false, cluster_id: null },
    { id: "user_sarah", label: "Sarah K.", score: 580, risk: "medium", is_suspicious: false, cluster_id: null },
    { id: "user_dev", label: "Dev R.", score: 715, risk: "low", is_suspicious: false, cluster_id: null },
    { id: "user_lisa", label: "Lisa N.", score: 890, risk: "low", is_suspicious: false, cluster_id: null },
    { id: "user_mark", label: "Mark C.", score: 650, risk: "medium", is_suspicious: false, cluster_id: null },
    { id: "sybil_0", label: "Sybil-1", score: 320, risk: "critical", is_suspicious: true, cluster_id: 1 },
    { id: "sybil_1", label: "Sybil-2", score: 310, risk: "critical", is_suspicious: true, cluster_id: 1 },
    { id: "sybil_2", label: "Sybil-3", score: 340, risk: "critical", is_suspicious: true, cluster_id: 1 },
    { id: "sybil_3", label: "Sybil-4", score: 305, risk: "critical", is_suspicious: true, cluster_id: 1 },
    { id: "low_0", label: "Risky-1", score: 420, risk: "high", is_suspicious: true, cluster_id: 2 },
    { id: "low_1", label: "Risky-2", score: 480, risk: "high", is_suspicious: true, cluster_id: 2 },
    { id: "low_2", label: "Risky-3", score: 510, risk: "high", is_suspicious: true, cluster_id: 2 },
  ],
  edges: [
    { source: "user_main", target: "user_alex", weight: 0.8, edge_type: "trust" },
    { source: "user_main", target: "user_priya", weight: 0.7, edge_type: "trust" },
    { source: "user_main", target: "user_lisa", weight: 0.9, edge_type: "trust" },
    { source: "user_alex", target: "user_james", weight: 0.85, edge_type: "trust" },
    { source: "user_alex", target: "user_dev", weight: 0.6, edge_type: "trust" },
    { source: "user_priya", target: "user_sarah", weight: 0.65, edge_type: "trust" },
    { source: "user_james", target: "user_lisa", weight: 0.75, edge_type: "trust" },
    { source: "user_dev", target: "user_mark", weight: 0.55, edge_type: "trust" },
    { source: "user_sarah", target: "sybil_0", weight: 0.3, edge_type: "transaction" },
    { source: "sybil_0", target: "sybil_1", weight: 0.95, edge_type: "suspicious" },
    { source: "sybil_0", target: "sybil_2", weight: 0.95, edge_type: "suspicious" },
    { source: "sybil_1", target: "sybil_3", weight: 0.95, edge_type: "suspicious" },
    { source: "sybil_2", target: "sybil_3", weight: 0.95, edge_type: "suspicious" },
    { source: "user_mark", target: "low_0", weight: 0.4, edge_type: "transaction" },
    { source: "low_0", target: "low_1", weight: 0.8, edge_type: "suspicious" },
    { source: "low_1", target: "low_2", weight: 0.8, edge_type: "suspicious" },
  ],
  clusters: [
    { cluster_id: 1, node_ids: ["sybil_0", "sybil_1", "sybil_2", "sybil_3"], reason: "Shared funding source and identical transaction patterns", severity: "critical" },
    { cluster_id: 2, node_ids: ["low_0", "low_1", "low_2"], reason: "Unusually dense connections with similar low trust scores", severity: "high" },
  ],
  total_nodes: 15,
  total_edges: 16,
}

function nodeColor(node: GraphNode): string {
  if (node.is_suspicious) return "oklch(0.55 0.22 25)"
  if (node.risk === "low") return "oklch(0.72 0.19 45)"
  if (node.risk === "medium") return "oklch(0.80 0.17 80)"
  return "oklch(0.55 0.22 25)"
}

function riskBadge(risk: string) {
  const colors: Record<string, string> = {
    low: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    medium: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    high: "text-destructive bg-destructive/10 border-destructive/20",
    critical: "text-destructive bg-destructive/10 border-destructive/20",
  }
  return colors[risk] || colors.medium
}

export function TrustGraphPage() {
  const { isDemo } = useDemoStore()
  const [graph, setGraph] = useState<GraphVisualization>(DEMO_GRAPH)
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      setLoading(true)
      if (!isDemo) {
        try {
          const data = await api.intelligence.getUserGraph("user_main")
          setGraph(data)
        } catch {
          setGraph(DEMO_GRAPH)
        }
      } else {
        await new Promise(r => setTimeout(r, 500))
        setGraph(DEMO_GRAPH)
      }
      setLoading(false)
    }
    load()
  }, [isDemo])

  const nodePositions = useCallback(() => {
    const positions: Record<string, { x: number; y: number }> = {}
    const w = 700
    const h = 500
    const trusted = graph.nodes.filter(n => !n.is_suspicious)
    const suspicious = graph.nodes.filter(n => n.is_suspicious)

    trusted.forEach((n, i) => {
      const angle = (i / trusted.length) * Math.PI * 1.5 + Math.PI * 0.25
      const radius = 150 + (i % 2) * 40
      positions[n.id] = {
        x: w / 2 + Math.cos(angle) * radius,
        y: h / 2.3 + Math.sin(angle) * radius,
      }
    })

    const clusterGroups: Record<number, GraphNode[]> = {}
    suspicious.forEach(n => {
      const cid = n.cluster_id ?? 0
      if (!clusterGroups[cid]) clusterGroups[cid] = []
      clusterGroups[cid].push(n)
    })

    let cx = w * 0.2
    Object.values(clusterGroups).forEach((group) => {
      group.forEach((n, i) => {
        positions[n.id] = {
          x: cx + (i % 2) * 50,
          y: h * 0.75 + Math.floor(i / 2) * 45,
        }
      })
      cx += 250
    })

    return positions
  }, [graph])

  const pos = nodePositions()

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="glass-card rounded-2xl p-12 flex flex-col items-center gap-4">
          <div className="w-8 h-8 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
          <p className="text-muted-foreground">Loading trust graph...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Trust Network Graph</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {graph.total_nodes} nodes, {graph.total_edges} connections, {graph.clusters.length} suspicious clusters
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full" style={{ background: "oklch(0.72 0.19 45)" }} /> Trusted</div>
          <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full" style={{ background: "oklch(0.80 0.17 80)" }} /> Medium</div>
          <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full" style={{ background: "oklch(0.55 0.22 25)" }} /> Suspicious</div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card rounded-2xl p-4 overflow-hidden">
          <svg viewBox="0 0 700 500" className="w-full h-auto">
            {graph.edges.map((e, i) => {
              const from = pos[e.source]
              const to = pos[e.target]
              if (!from || !to) return null
              const isSuspicious = e.edge_type === "suspicious"
              return (
                <line key={i} x1={from.x} y1={from.y} x2={to.x} y2={to.y}
                  stroke={isSuspicious ? "oklch(0.55 0.22 25 / 0.6)" : "oklch(0.40 0 0 / 0.4)"}
                  strokeWidth={isSuspicious ? 2 : 1}
                  strokeDasharray={isSuspicious ? "4 4" : "none"}
                />
              )
            })}

            {graph.nodes.map(node => {
              const p = pos[node.id]
              if (!p) return null
              const r = node.id === "user_main" ? 18 : node.is_suspicious ? 12 : 14
              return (
                <g key={node.id}
                  onMouseEnter={() => setHoveredNode(node)}
                  onMouseLeave={() => setHoveredNode(null)}
                  className="cursor-pointer"
                >
                  {node.is_suspicious && (
                    <circle cx={p.x} cy={p.y} r={r + 4} fill="none"
                      stroke="oklch(0.55 0.22 25 / 0.3)" strokeWidth="2" strokeDasharray="3 3" />
                  )}
                  <circle cx={p.x} cy={p.y} r={r} fill={nodeColor(node)}
                    opacity={hoveredNode && hoveredNode.id !== node.id ? 0.4 : 1}
                    className="transition-opacity duration-200" />
                  <text x={p.x} y={p.y + r + 14} textAnchor="middle"
                    fill="oklch(0.56 0 0)" fontSize="9" fontWeight="500">
                    {node.label}
                  </text>
                  {node.id === "user_main" && (
                    <text x={p.x} y={p.y + 4} textAnchor="middle"
                      fill="oklch(0.08 0 0)" fontSize="10" fontWeight="700">
                      You
                    </text>
                  )}
                </g>
              )
            })}
          </svg>
        </div>

        <div className="flex flex-col gap-4">
          {hoveredNode && (
            <div className="glass-card rounded-2xl p-5 border-glow">
              <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Node Details</p>
              <p className="text-lg font-bold text-foreground">{hoveredNode.label}</p>
              <div className="mt-3 flex flex-col gap-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Trust Score</span>
                  <span className="font-semibold text-foreground">{hoveredNode.score}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Risk Level</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${riskBadge(hoveredNode.risk)}`}>
                    {hoveredNode.risk}
                  </span>
                </div>
                {hoveredNode.is_suspicious && (
                  <div className="flex items-center gap-1.5 mt-1 text-xs text-destructive">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Flagged as suspicious
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="glass-card rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-destructive" />
              <p className="font-semibold text-foreground text-sm">Suspicious Clusters</p>
            </div>
            <div className="flex flex-col gap-3">
              {graph.clusters.map(c => (
                <div key={c.cluster_id} className="p-3 rounded-xl bg-destructive/5 border border-destructive/15">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-destructive">
                      Cluster #{c.cluster_id}
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                      c.severity === "critical" ? "bg-destructive/20 text-destructive" : "bg-amber-500/20 text-amber-400"
                    }`}>{c.severity}</span>
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">{c.reason}</p>
                  <p className="text-[10px] text-muted-foreground mt-1">{c.node_ids.length} nodes involved</p>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card rounded-2xl p-5">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Network Stats</p>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: "Total Nodes", value: graph.total_nodes },
                { label: "Total Edges", value: graph.total_edges },
                { label: "Clusters", value: graph.clusters.length },
                { label: "Suspicious", value: graph.nodes.filter(n => n.is_suspicious).length },
              ].map(({ label, value }) => (
                <div key={label} className="p-2 rounded-lg bg-secondary text-center">
                  <p className="text-lg font-bold text-foreground">{value}</p>
                  <p className="text-[10px] text-muted-foreground">{label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
