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
  gameLog?: Array<Record<string, any>>
  statKey?: "points" | "goals" | "assists"
}

export function PlayerProjectionRechart({
  metricLabel,
  projectionTotal,
  gamesPlayed,
  currentTotal,
  height = 320,
  gameLog = [],
  statKey = "points",
}: Props) {
  // local timeframe controls: Last 10, YTD, ALL (UI only; line remains cumulative)
  const [timeframe, setTimeframe] = React.useState<string>("ALL")
  const tfs = ["Last 10", "YTD", "ALL"]
  const firstGame = 1
  const lastGame = 82

  // Prepare cumulative actuals from gameLog (sorted oldest->newest)
  const sortedLog = React.useMemo(() => {
    try {
      return [...(gameLog || [])].sort((a, b) => String(a.gameDate).localeCompare(String(b.gameDate)))
    } catch {
      return [] as Array<Record<string, any>>
    }
  }, [gameLog])

  const cumulative = React.useMemo(() => {
    const arr: number[] = []
    let sum = 0
    for (const rec of sortedLog) {
      const val = Number(rec?.[statKey] ?? 0)
      sum += Number.isFinite(val) ? val : 0
      arr.push(sum)
    }
    return arr
  }, [sortedLog, statKey])

  const totalGamesPlayed = Math.max(gamesPlayed || 0, cumulative.length)

  // Determine window based on timeframe
  const [startGame, endGame] = React.useMemo((): [number, number] => {
    if (timeframe === "Last 10") {
      const e = Math.max(firstGame, Math.min(totalGamesPlayed || firstGame, lastGame))
      const s = Math.max(firstGame, e - 9)
      return [s, Math.max(s, e)]
    }
    if (timeframe === "YTD") {
      const e = Math.max(firstGame, Math.min(totalGamesPlayed || firstGame, lastGame))
      return [firstGame, e]
    }
    return [firstGame, lastGame]
  }, [timeframe, totalGamesPlayed])

  // Build data points for selected window
  const data = React.useMemo(() => {
    const rows: { g: number; forecast: number; current?: number }[] = []
    for (let g = startGame; g <= endGame; g += 1) {
      const forecastVal = (projectionTotal * g) / lastGame
      const currentVal = g - 1 < cumulative.length ? cumulative[g - 1] : undefined
      rows.push({ g, forecast: forecastVal, current: currentVal })
    }
    return rows
  }, [startGame, endGame, projectionTotal, cumulative])

  // Build a "nice" Y max and ticks similar to the top chart spacing
  const currentMaxInWindow = data.reduce((mx, d) => (d.current !== undefined && d.current > mx ? d.current : mx), 0)
  const windowMax = Math.max((projectionTotal * endGame) / lastGame, currentMaxInWindow)
  const rawMax = (windowMax || 1) * 1.1
  const niceMaxBase = Math.max(10, Math.ceil(rawMax))
  const niceMax = Math.ceil(niceMaxBase / 10) * 10
  const yTicks = [0, Math.round(niceMax * 0.25), Math.round(niceMax * 0.5), Math.round(niceMax * 0.75), niceMax]
  const range = endGame - startGame
  const xTicks = React.useMemo(() => {
    const ticks: number[] = []
    const step = range >= 40 ? 10 : range >= 20 ? 5 : range >= 10 ? 2 : 1
    for (let t = startGame; t <= endGame; t += step) ticks.push(t)
    if (ticks[ticks.length - 1] !== endGame) ticks.push(endGame)
    return ticks
  }, [startGame, endGame, range])

  return (
    <div className="rounded-lg border border-border bg-card/50 p-6">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <div className="text-sm font-medium">Season Progress – {metricLabel}</div>
          <div className="text-xs text-muted-foreground">Actual YTD: {Math.round(currentTotal)}</div>
        </div>
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
            domain={[startGame, endGame]}
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


