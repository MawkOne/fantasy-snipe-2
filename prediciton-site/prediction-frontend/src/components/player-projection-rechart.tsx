"use client"

import React from "react"

import {
  ComposedChart,
  Area,
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
  height = 200,
  gameLog = [],
  statKey = "points",
}: Props) {
  // local timeframe controls: Last 10, YTD (UI only; line remains cumulative)
  const [timeframe, setTimeframe] = React.useState<string>("YTD")
  const tfs = ["Last 10", "YTD"]
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
    const e = Math.max(firstGame, Math.min(totalGamesPlayed || firstGame, lastGame))
    if (timeframe === "Last 10") {
      const s = Math.max(firstGame, e - 9)
      return [s, Math.max(s, e)]
    }
    // YTD
    return [firstGame, e]
  }, [timeframe, totalGamesPlayed])

  // Build data points for selected window
  const data = React.useMemo(() => {
    const rows: { g: number; forecast: number; current?: number; actualAbove?: number; actualBelow?: number }[] = []
    for (let g = startGame; g <= endGame; g += 1) {
      const forecastVal = (projectionTotal * g) / lastGame
      const currentVal = g - 1 < cumulative.length ? cumulative[g - 1] : undefined
      
      // For filling between lines
      let actualAbove = undefined
      let actualBelow = undefined
      
      if (currentVal !== undefined) {
        if (currentVal >= forecastVal) {
          // Player is above forecast - show actual, will fill green above forecast
          actualAbove = currentVal
        } else {
          // Player is below forecast - show actual, will fill red below forecast
          actualBelow = currentVal
        }
      }
      
      rows.push({ g, forecast: forecastVal, current: currentVal, actualAbove, actualBelow })
    }
    return rows
  }, [startGame, endGame, projectionTotal, cumulative])

  // Build a "nice" Y max and ticks - scale to the max within the selected window
  const currentMaxInWindow = data.reduce((mx, d) => (d.current !== undefined && d.current > mx ? d.current : mx), 0)
  const projectionAtWindowEnd = (projectionTotal * endGame) / lastGame
  const baseMax = Math.max(projectionAtWindowEnd, currentMaxInWindow)
  const rawMax = Math.max(1, baseMax) * 1.1
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
    <div className="rounded-lg border border-border bg-card/50 p-3">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <div className="text-xs font-medium">Season Progress – {metricLabel}</div>
          <div className="text-xs text-muted-foreground">Actual YTD: {Math.round(currentTotal)}</div>
        </div>
        <div className="flex gap-1">
          {tfs.map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                timeframe === tf ? "bg-accent text-foreground" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data} margin={{ top: -5, right: 5, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.15} horizontal={true} vertical={false} />
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
          <Tooltip 
            formatter={(v: any, name: string) => {
              if (name === "Above" || name === "Below") return null
              return Number(v).toFixed(1)
            }}
            labelFormatter={(l) => `Game ${l}`}
            wrapperStyle={{ zIndex: 1000 }}
            contentStyle={{
              backgroundColor: "#ffffff",
              border: "1px solid #e5e7eb",
              borderRadius: "12px",
              padding: "12px 16px",
              boxShadow: "0 10px 40px -10px rgba(0, 0, 0, 0.4), 0 0 1px rgba(0, 0, 0, 0.1)",
            }}
            labelStyle={{
              color: "#111827",
              fontWeight: "600",
              fontSize: "14px",
              marginBottom: "8px",
            }}
            itemStyle={{
              padding: "4px 0",
              fontSize: "13px",
            }}
            cursor={{ stroke: "rgba(0, 0, 0, 0.1)", strokeWidth: 2 }}
          />
          {/* Forecast line (dashed black) */}
          <Line 
            type="monotone" 
            dataKey="forecast" 
            name="Forecast" 
            stroke="#000000" 
            strokeWidth={2} 
            dot={false} 
            strokeDasharray="5 5"
          />
          {/* Actual performance line (solid black) */}
          <Line 
            type="monotone" 
            dataKey="current" 
            name="Actual" 
            stroke="#000000" 
            strokeWidth={3}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}


