"use client";

import { RISK_TIER_COLORS, RISK_TIER_LABELS } from "@/lib/constants";

interface TrustScoreRingProps {
  score: number;
  maxScore?: number;
  tier: string;
  size?: number;
}

/**
 * Interpolate between two hex colors.
 */
function lerpColor(a: string, b: string, t: number): string {
  const ah = parseInt(a.slice(1), 16);
  const bh = parseInt(b.slice(1), 16);
  const ar = (ah >> 16) & 0xff, ag = (ah >> 8) & 0xff, ab = ah & 0xff;
  const br = (bh >> 16) & 0xff, bg = (bh >> 8) & 0xff, bb = bh & 0xff;
  const rr = Math.round(ar + (br - ar) * t);
  const rg = Math.round(ag + (bg - ag) * t);
  const rb = Math.round(ab + (bb - ab) * t);
  return `rgb(${rr},${rg},${rb})`;
}

/**
 * Build a small arc segment path between two angles on a circle.
 */
function arcSegment(cx: number, cy: number, r: number, startDeg: number, endDeg: number): string {
  const toRad = (d: number) => (d * Math.PI) / 180;
  const x1 = cx + r * Math.cos(toRad(startDeg));
  const y1 = cy + r * Math.sin(toRad(startDeg));
  const x2 = cx + r * Math.cos(toRad(endDeg));
  const y2 = cy + r * Math.sin(toRad(endDeg));
  const sweep = endDeg - startDeg > 180 ? 1 : 0;
  return `M ${x1} ${y1} A ${r} ${r} 0 ${sweep} 1 ${x2} ${y2}`;
}

const GAUGE_COLORS = [
  { stop: 0, color: "#ef4444" },   // red
  { stop: 0.3, color: "#f59e0b" }, // amber
  { stop: 0.6, color: "#22c55e" }, // green
  { stop: 1, color: "#10b981" },   // emerald
];

function getGaugeColor(t: number): string {
  for (let i = 0; i < GAUGE_COLORS.length - 1; i++) {
    if (t <= GAUGE_COLORS[i + 1].stop) {
      const local = (t - GAUGE_COLORS[i].stop) / (GAUGE_COLORS[i + 1].stop - GAUGE_COLORS[i].stop);
      return lerpColor(GAUGE_COLORS[i].color, GAUGE_COLORS[i + 1].color, local);
    }
  }
  return GAUGE_COLORS[GAUGE_COLORS.length - 1].color;
}

export function TrustScoreRing({
  score,
  maxScore = 1000,
  tier,
  size = 200,
}: TrustScoreRingProps) {
  const pct = Math.min(score / maxScore, 1);
  const tierColor = RISK_TIER_COLORS[tier] ?? "text-gray-400";
  const tierLabel = RISK_TIER_LABELS[tier] ?? tier;

  const strokeW = 6;
  const padding = 8;
  const radius = (size - strokeW) / 2 - padding;
  const cx = size / 2;
  const cy = size / 2;

  // Arc sweeps from 180° to 0° (left to right, top half).
  // In SVG coordinate system (y-down), 180° is left, 0° is right.
  const arcStart = 180; // left
  const arcEnd = 360;   // right (in SVG y-down coords, 360° = same as 0°)

  // Needle
  const needleDeg = arcStart + pct * (arcEnd - arcStart);
  const needleRad = (needleDeg * Math.PI) / 180;
  const needleLen = radius - 14;
  const needleX = cx + needleLen * Math.cos(needleRad);
  const needleY = cy + needleLen * Math.sin(needleRad);

  const needleColor = pct >= 0.6 ? "#22c55e" : pct >= 0.3 ? "#f59e0b" : "#ef4444";

  // Build colored segments (many small arcs for smooth gradient)
  const segCount = 60;
  const scoreSeg = Math.round(pct * segCount);
  const degPerSeg = (arcEnd - arcStart) / segCount;

  // viewBox: show only top half + small bottom margin for needle hub
  const viewH = cy + 10;

  return (
    <div className="flex flex-col items-center w-full">
      <svg
        width="100%"
        viewBox={`0 0 ${size} ${viewH}`}
        style={{ maxWidth: size, display: "block", margin: "0 auto" }}
      >
        {/* Background track */}
        <path
          d={arcSegment(cx, cy, radius, arcStart, arcEnd)}
          fill="none"
          stroke="#1e293b"
          strokeWidth={strokeW}
          strokeLinecap="round"
        />

        {/* Colored score segments */}
        {Array.from({ length: scoreSeg }, (_, i) => {
          const segStart = arcStart + i * degPerSeg;
          const segEnd = segStart + degPerSeg + 0.5; // tiny overlap to avoid gaps
          const t = i / segCount;
          return (
            <path
              key={i}
              d={arcSegment(cx, cy, radius, segStart, Math.min(segEnd, arcStart + pct * 180))}
              fill="none"
              stroke={getGaugeColor(t)}
              strokeWidth={strokeW}
              strokeLinecap={i === 0 || i === scoreSeg - 1 ? "round" : "butt"}
            />
          );
        })}

        {/* Needle line */}
        <line
          x1={cx}
          y1={cy}
          x2={needleX}
          y2={needleY}
          stroke={needleColor}
          strokeWidth={2}
          strokeLinecap="round"
        />

        {/* Needle hub */}
        <circle cx={cx} cy={cy} r={4} fill={needleColor} />
        <circle cx={cx} cy={cy} r={1.5} fill="#0B0F1A" />

        {/* Scale labels */}
        <text
          x={cx - radius - 2}
          y={cy + 16}
          fill="#6b7280"
          fontSize="9"
          textAnchor="middle"
        >
          0
        </text>
        <text
          x={cx}
          y={cy - radius - 8}
          fill="#6b7280"
          fontSize="9"
          textAnchor="middle"
        >
          500
        </text>
        <text
          x={cx + radius + 2}
          y={cy + 16}
          fill="#6b7280"
          fontSize="9"
          textAnchor="middle"
        >
          1000
        </text>
      </svg>

      {/* Score + tier */}
      <div className="flex flex-col items-center mt-1">
        <span className="text-4xl font-bold tracking-tight">{score}</span>
        <span className={`text-sm font-semibold uppercase tracking-wide ${tierColor}`}>
          {tierLabel}
        </span>
      </div>
    </div>
  );
}
