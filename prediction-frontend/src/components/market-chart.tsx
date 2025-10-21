"use client"

import { Card } from "@/components/ui/card"
import { useState } from "react"

interface MarketChartProps {
  projectionLine?: number
  moreProbability?: number
}

export function MarketChart({ projectionLine = 60, moreProbability = 34 }: MarketChartProps) {
  const [timeframe, setTimeframe] = useState("ALL")
  const timeframes = ["Last 10", "YTD", "ALL"]

  return (
    <div className="space-y-4">
      <Card className="p-6">
        <div className="flex items-center justify-end mb-2">
          <div className="flex gap-1">
            {timeframes.map((tf) => (
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

        <div className="relative h-80 rounded-lg overflow-hidden">
          <div className="absolute left-0 top-0 bottom-0 w-16 flex flex-col justify-between text-xs text-muted-foreground py-4">
            <span className="text-green-600 font-medium">100%</span>
            <span>75%</span>
            <span className="font-medium">50%</span>
            <span>25%</span>
            <span className="text-red-600 font-medium">0%</span>
          </div>

          {/* Grid lines */}
          <div className="absolute left-16 right-0 top-0 bottom-0 flex flex-col justify-between">
            {[0, 1, 2, 3, 4].map((i) => (
              <div key={i} className={`border-t ${i === 2 ? "border-border" : "border-border/30"}`} />
            ))}
          </div>

          {/* Chart content */}
          <div className="ml-16 h-full relative">
            <svg className="w-full h-full" viewBox="0 0 400 200" preserveAspectRatio="none">
              {/* 50% reference line */}
              <line
                x1="0"
                y1="100"
                x2="400"
                y2="100"
                stroke="hsl(var(--muted-foreground))"
                strokeWidth="1"
                strokeDasharray="4 4"
                opacity="0.3"
              />

              {/* Chart line oscillating around 50% (y=100) */}
              <path
                d="M 0 120 L 40 115 L 80 118 L 120 122 L 160 125 L 200 130 L 240 132 L 280 128 L 320 130 L 360 132 L 400 128"
                fill="none"
                stroke="hsl(var(--primary))"
                strokeWidth="3"
                vectorEffect="non-scaling-stroke"
              />

              {/* Fill area */}
              
            </svg>
          </div>

          {/* X-axis labels */}
          <div className="absolute bottom-0 left-16 right-0 flex justify-between text-xs text-muted-foreground px-4 pb-2">
            <span>Oct</span>
            <span>Nov</span>
            <span>Dec</span>
            <span>Jan</span>
            <span>Feb</span>
            <span>Mar</span>
          </div>
        </div>
      </Card>
    </div>
  )
}
