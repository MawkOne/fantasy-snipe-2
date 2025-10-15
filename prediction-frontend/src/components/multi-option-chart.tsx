"use client"

import { Card } from "@/components/ui/card"
import { useState } from "react"

interface MultiOptionOutcome {
  id: string
  name: string
  probability: number
}

interface MultiOptionChartProps {
  outcomes: MultiOptionOutcome[]
}

export function MultiOptionChart({ outcomes }: MultiOptionChartProps) {
  const [timeframe, setTimeframe] = useState("ALL")
  const timeframes = ["1H", "6H", "1W", "1M", "ALL"]

  const generateChartData = () => {
    const points = 50
    return outcomes.map((outcome) => {
      const data = []
      const currentProb = outcome.probability
      for (let i = 0; i < points; i++) {
        // Simulate probability changes over time
        const variance = (Math.random() - 0.5) * 10
        const value = Math.max(0, Math.min(100, currentProb + variance * (1 - i / points)))
        data.push({ x: i, y: value })
      }
      return { ...outcome, data }
    })
  }

  const chartData = generateChartData()
  const colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#6b7280"]

  return (
    <Card className="p-4 sm:p-6">
      {/* Timeframe Selector */}
      <div className="flex justify-end gap-2 mb-4">
        {timeframes.map((tf) => (
          <button
            key={tf}
            onClick={() => setTimeframe(tf)}
            className={`px-2 sm:px-3 py-1 text-xs sm:text-sm rounded transition-colors ${
              timeframe === tf
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-accent"
            }`}
          >
            {tf}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className="relative h-64 sm:h-80">
        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 bottom-0 w-10 sm:w-12 flex flex-col justify-between text-xs text-muted-foreground">
          <span>100%</span>
          <span>75%</span>
          <span>50%</span>
          <span>25%</span>
          <span>0%</span>
        </div>

        {/* Chart content */}
        <div className="ml-10 sm:ml-12 h-full relative">
          <svg className="w-full h-full" viewBox="0 0 400 200" preserveAspectRatio="none">
            {/* Grid lines */}
            <line x1="0" y1="0" x2="400" y2="0" stroke="currentColor" strokeWidth="0.5" className="text-border" />
            <line
              x1="0"
              y1="50"
              x2="400"
              y2="50"
              stroke="currentColor"
              strokeWidth="0.5"
              className="text-border"
              strokeDasharray="2,2"
            />
            <line
              x1="0"
              y1="100"
              x2="400"
              y2="100"
              stroke="currentColor"
              strokeWidth="0.5"
              className="text-border"
              strokeDasharray="2,2"
            />
            <line
              x1="0"
              y1="150"
              x2="400"
              y2="150"
              stroke="currentColor"
              strokeWidth="0.5"
              className="text-border"
              strokeDasharray="2,2"
            />
            <line x1="0" y1="200" x2="400" y2="200" stroke="currentColor" strokeWidth="0.5" className="text-border" />

            {/* Plot lines for each outcome */}
            {chartData.slice(0, 5).map((outcome, index) => {
              const pathData = outcome.data
                .map((point, i) => {
                  const x = (i / (outcome.data.length - 1)) * 400
                  const y = 200 - (point.y / 100) * 200
                  return `${i === 0 ? "M" : "L"} ${x} ${y}`
                })
                .join(" ")

              return (
                <path
                  key={outcome.id}
                  d={pathData}
                  fill="none"
                  stroke={colors[index]}
                  strokeWidth="2"
                  className="transition-all"
                />
              )
            })}
          </svg>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-3 sm:gap-4">
        {outcomes.slice(0, 5).map((outcome, index) => (
          <div key={outcome.id} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: colors[index] }} />
            <span className="text-xs sm:text-sm text-muted-foreground">{outcome.name}</span>
          </div>
        ))}
      </div>
    </Card>
  )
}
