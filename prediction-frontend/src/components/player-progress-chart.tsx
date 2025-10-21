"use client"

import React from "react"

interface PlayerProgressChartProps {
  metricLabel: string // "Points" | "Goals" | "Assists"
  projectionTotal: number // projected season total for metric
  gamesPlayed: number // current GP
  currentTotal: number // current season total for metric
  height?: number
}

export function PlayerProgressChart({
  metricLabel,
  projectionTotal,
  gamesPlayed,
  currentTotal,
  height = 160,
}: PlayerProgressChartProps) {
  const width = 640
  const padding = { left: 36, right: 12, top: 12, bottom: 24 }
  const innerW = width - padding.left - padding.right
  const innerH = height - padding.top - padding.bottom

  const maxX = 82
  const maxY = Math.max(projectionTotal, currentTotal) * 1.1 || 1
  const x = (g: number) => padding.left + (g / maxX) * innerW
  const y = (v: number) => padding.top + innerH - (v / maxY) * innerH

  // Forecast line: from (0,0) to (82, projectionTotal)
  const forecastPath = `M ${x(0)},${y(0)} L ${x(82)},${y(projectionTotal)}`
  // Current line: from (0,0) to (GP, currentTotal)
  const currentPath = `M ${x(0)},${y(0)} L ${x(gamesPlayed)},${y(currentTotal)}`

  // Y ticks (0, 25%, 50%, 75%, 100% of max)
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => Math.round(t * maxY))

  return (
    <div className="rounded-lg border border-border bg-card/50 p-4">
      <div className="text-sm font-medium mb-2">Season Progress – {metricLabel}</div>
      <svg width="100%" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Cumulative ${metricLabel} progress`}>
        {/* axes */}
        <line x1={x(0)} y1={y(0)} x2={x(maxX)} y2={y(0)} stroke="currentColor" className="text-border" />
        <line x1={x(0)} y1={y(0)} x2={x(0)} y2={y(maxY)} stroke="currentColor" className="text-border" />

        {/* y ticks & labels */}
        {ticks.map((tv, i) => (
          <g key={i}>
            <line x1={x(0)} y1={y(tv)} x2={x(maxX)} y2={y(tv)} stroke="currentColor" className="text-border/40" />
            <text x={x(0) - 6} y={y(tv)} textAnchor="end" dominantBaseline="middle" className="fill-muted-foreground text-[10px]">
              {tv}
            </text>
          </g>
        ))}

        {/* forecast line */}
        <path d={forecastPath} stroke="#16a34a" strokeWidth={3} fill="none" />
        {/* current line */}
        <path d={currentPath} stroke="#2563eb" strokeWidth={3} fill="none" />

        {/* x labels for months (approx at game numbers) */}
        {[0, 20, 40, 60, 82].map((gx, i) => (
          <text key={i} x={x(gx)} y={y(0) + 16} textAnchor="middle" className="fill-muted-foreground text-[10px]">
            {gx}
          </text>
        ))}
      </svg>
      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1"><span className="w-3 h-1 rounded-full bg-[#16a34a] inline-block" /> Forecast (to {projectionTotal.toFixed(1)})</span>
        <span className="inline-flex items-center gap-1"><span className="w-3 h-1 rounded-full bg-[#2563eb] inline-block" /> Current ({currentTotal} in {gamesPlayed} GP)</span>
      </div>
    </div>
  )
}


