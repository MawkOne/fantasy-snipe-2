"use client"

import { Card } from "@/components/ui/card"
import { useState, useMemo } from "react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

interface MarketChartProps {
  projectionLine?: number
  moreProbability?: number
  trades: any[]
  volume?: string
  traders?: number
}

export function MarketChart({ projectionLine = 60, moreProbability = 34, trades = [], volume, traders }: MarketChartProps) {
  const [timeframe, setTimeframe] = useState("ALL")
  const timeframes = ["Last 10", "YTD", "ALL"]

  const chartData = useMemo(() => {
    if (!Array.isArray(trades) || trades.length === 0) {
      return [{ time: 0, more: moreProbability, less: 100 - moreProbability, label: "Now", date: new Date().toISOString() }]
    }
    
    // Sort trades chronologically (oldest first)
    const sortedTrades = [...trades].sort((a, b) => 
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    )
    
    // Group trades by date and take the last price of each day
    const tradesByDate = new Map<string, any>()
    sortedTrades.forEach((trade) => {
      const date = new Date(trade.created_at)
      const dateKey = date.toISOString().split('T')[0] // YYYY-MM-DD
      tradesByDate.set(dateKey, trade)
    })
    
    // Convert to chart data points with both More and Less probabilities
    const data = Array.from(tradesByDate.entries()).map(([dateKey, trade], i) => {
      const date = new Date(dateKey)
      const monthDay = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      const moreProb = Math.round((trade.outcome === "yes" ? trade.price : 1 - trade.price) * 100)
      return {
        time: i,
        more: moreProb,
        less: 100 - moreProb,
        label: monthDay,
        date: trade.created_at,
      }
    })
    
    return data
  }, [trades, moreProbability])

  return (
    <div className="space-y-4">
      <Card className="p-3">
        <div className="flex items-center justify-between mb-1 flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">More:</span>
              <span className="text-base font-bold text-emerald-700 dark:text-emerald-300">{moreProbability}%</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-red-600 dark:text-red-400">Less:</span>
              <span className="text-base font-bold text-red-700 dark:text-red-300">{100 - moreProbability}%</span>
            </div>
            {(volume || traders !== undefined) && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground ml-1">
                {volume && <span>{volume} volume</span>}
                {volume && traders !== undefined && <span>•</span>}
                {traders !== undefined && <span>{traders} traders</span>}
                <span>•</span>
                <span>Ends Apr 2026</span>
              </div>
            )}
          </div>
          <div className="flex gap-1">
            {timeframes.map((tf) => (
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
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData} margin={{ top: -5, right: 5, bottom: 0, left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.15} horizontal={true} vertical={false} />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(val) => chartData[val]?.label || ""}
              interval={Math.max(0, Math.floor(chartData.length / 8))}
            />
            <YAxis
              domain={[0, 100]}
              ticks={[20, 40, 60, 80]}
              tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(val) => `${val}%`}
            />
            <Tooltip
              formatter={(value: any, name: string) => [`${value}%`, name]}
              labelFormatter={(label) => chartData[label]?.label || ""}
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
            <Line
              type="monotone"
              dataKey="more"
              stroke="#10b981"
              strokeWidth={2.5}
              dot={false}
              animationDuration={1000}
              name="More"
            />
            <Line
              type="monotone"
              dataKey="less"
              stroke="#ef4444"
              strokeWidth={2.5}
              dot={false}
              animationDuration={1000}
              name="Less"
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  )
}
