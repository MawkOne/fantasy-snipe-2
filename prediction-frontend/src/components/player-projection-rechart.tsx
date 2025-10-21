"use client"

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
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
  const data = [
    { g: 0, forecast: 0, current: 0 },
    { g: gamesPlayed, forecast: (projectionTotal * gamesPlayed) / 82, current: currentTotal },
    { g: 82, forecast: projectionTotal, current: currentTotal },
  ]

  const maxY = Math.max(projectionTotal, currentTotal) * 1.1 || 1

  return (
    <div className="rounded-lg border border-border bg-card/50 p-4">
      <div className="text-sm font-medium mb-2">Season Progress – {metricLabel}</div>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="g" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
          <YAxis domain={[0, maxY]} tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
          <Tooltip formatter={(v: any) => Number(v).toFixed(1)} labelFormatter={(l) => `Game ${l}`} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="forecast" name="Forecast" stroke="#16a34a" strokeWidth={3} dot={false} />
          <Line type="monotone" dataKey="current" name="Current" stroke="#2563eb" strokeWidth={3} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}


