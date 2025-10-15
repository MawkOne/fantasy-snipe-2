"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useState } from "react"

interface Outcome {
  id: string
  label: string
  probability: number
  buyPrice: number
  sellPrice: number
}

interface TradingPanelProps {
  outcomes: Outcome[]
}

export function TradingPanel({ outcomes }: TradingPanelProps) {
  const [side, setSide] = useState<"buy" | "sell">("buy")
  const [selectedOutcome, setSelectedOutcome] = useState(outcomes[0].id)
  const [amount, setAmount] = useState("")

  const presetAmounts = [1, 5, 10, 25]

  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* Buy/Sell Toggle */}
        <div className="flex gap-2 p-1 bg-accent rounded-lg">
          <button
            onClick={() => setSide("buy")}
            className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
              side === "buy" ? "bg-green-600 text-white" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Buy
          </button>
          <button
            onClick={() => setSide("sell")}
            className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
              side === "sell" ? "bg-red-600 text-white" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Sell
          </button>
        </div>

        {/* Outcome Selector */}
        <div>
          <label className="text-sm font-medium mb-2 block">Outcome</label>
          <select
            value={selectedOutcome}
            onChange={(e) => setSelectedOutcome(e.target.value)}
            className="w-full p-2 rounded-lg border border-border bg-background"
          >
            {outcomes.map((outcome) => (
              <option key={outcome.id} value={outcome.id}>
                {outcome.label} - {outcome.probability}%
              </option>
            ))}
          </select>
        </div>

        {/* Amount Input */}
        <div>
          <label className="text-sm font-medium mb-2 block">Amount</label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-2xl text-muted-foreground">$</span>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0"
              className="w-full pl-8 pr-4 py-3 text-2xl font-bold rounded-lg border border-border bg-background"
            />
          </div>
          <div className="flex gap-2 mt-2">
            {presetAmounts.map((preset) => (
              <button
                key={preset}
                onClick={() => setAmount(preset.toString())}
                className="flex-1 py-1 text-xs font-medium rounded border border-border hover:bg-accent"
              >
                +${preset}
              </button>
            ))}
            <button
              onClick={() => setAmount("")}
              className="flex-1 py-1 text-xs font-medium rounded border border-border hover:bg-accent"
            >
              Max
            </button>
          </div>
        </div>

        {/* Trade Button */}
        <Button
          className={`w-full ${side === "buy" ? "bg-green-600 hover:bg-green-700" : "bg-red-600 hover:bg-red-700"}`}
          size="lg"
        >
          {side === "buy" ? "Submit Forecast" : "Sell Position"}
        </Button>

        <p className="text-xs text-muted-foreground text-center">By forecasting you agree to the Terms of Service</p>
      </div>
    </Card>
  )
}
