"use client"

import React from "react"

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts"

interface Props {
  metricLabel: string // Points | Goals | Assists
  projectionTotal: number
  gamesPlayed: number
  currentTotal: number
  height?: number
}

export function PlayerProjectionRechart({
  metricLabel,
  projectionTotal,
  gamesPlayed,
  currentTotal,
  height = 320,
}: Props) {
  // local timeframe controls: Last 10, YTD, ALL (UI only; line remains cumulative)
  const [timeframe, setTimeframe] = React.useState<string>("ALL")
  const tfs = ["Last 10", "YTD", "ALL"]
  // Build two-point series to draw straight lines
  const firstGame = 1
  const lastGame = 82
  const data = [
    { g: firstGame, forecast: (projectionTotal * firstGame) / lastGame, current: 0 },
    { g: Math.max(firstGame, Math.min(gamesPlayed, lastGame)), forecast: (projectionTotal * Math.max(firstGame, Math.min(gamesPlayed, lastGame))) / lastGame, current: currentTotal },
    { g: lastGame, forecast: projectionTotal, current: currentTotal },
  ]

  // Build a "nice" Y max and ticks similar to the top chart spacing
  const rawMax = Math.max(projectionTotal, currentTotal) * 1.1 || 1
  const niceMaxBase = Math.max(10, Math.ceil(rawMax))
  const niceMax = Math.ceil(niceMaxBase / 10) * 10
  const yTicks = [0, Math.round(niceMax * 0.25), Math.round(niceMax * 0.5), Math.round(niceMax * 0.75), niceMax]
  const xTicks = [1, 10, 20, 30, 40, 50, 60, 70, 82]

  return (
    <div className="rounded-lg border border-border bg-card/50 p-6">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-medium">Season Progress – {metricLabel}</div>
        <div className="flex gap-1">
          {tfs.map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                timeframe === tf ? "bg-accent text-foreground" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="4 4" stroke="hsl(var(--border))" />
          <XAxis
            type="number"
            dataKey="g"
            domain={[firstGame, lastGame]}
            allowDecimals={false}
            ticks={xTicks}
            tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
            tickMargin={4}
            padding={{ left: 8, right: 8 }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            domain={[0, niceMax]}
            ticks={yTicks}
            tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
            allowDecimals={false}
            tickMargin={4}
            width={36}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip formatter={(v: any) => Number(v).toFixed(1)} labelFormatter={(l) => `Game ${l}`} />
          {/* Mid reference line to echo the style of the top chart's 50% guide */}
          <ReferenceLine y={niceMax / 2} stroke="hsl(var(--muted-foreground))" strokeDasharray="4 4" strokeOpacity={0.3} />
          <Line type="monotone" dataKey="forecast" name="Forecast" stroke="#16a34a" strokeWidth={3} dot={false} />
          <Line type="monotone" dataKey="current" name="Current" stroke="hsl(var(--primary))" strokeWidth={3} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}


