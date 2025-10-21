"use client"

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
      <div className="text-sm font-medium mb-4">Season Progress – {metricLabel}</div>
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


