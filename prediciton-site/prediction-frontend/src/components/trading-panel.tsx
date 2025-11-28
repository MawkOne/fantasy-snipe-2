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
  amount?: string
  setAmount?: (amount: string) => void
  selectedOutcome?: string
  setSelectedOutcome?: (outcome: string) => void
}

export function TradingPanel({ outcomes, amount: externalAmount, setAmount: externalSetAmount, selectedOutcome: externalSelectedOutcome, setSelectedOutcome: externalSetSelectedOutcome }: TradingPanelProps) {
  const [side, setSide] = useState<"buy" | "sell">("buy")
  const [internalSelectedOutcome, setInternalSelectedOutcome] = useState(outcomes[0].id)
  const [internalAmount, setInternalAmount] = useState("")

  const amount = externalAmount !== undefined ? externalAmount : internalAmount
  const setAmount = externalSetAmount || setInternalAmount
  const selectedOutcome = externalSelectedOutcome || internalSelectedOutcome
  const setSelectedOutcome = externalSetSelectedOutcome || setInternalSelectedOutcome

  const presetAmounts = [1, 20, 100]

  return (
    <Card className="p-4">
      <div className="space-y-4">
        {/* Buy/Sell Toggle */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex gap-2">
            <button
              onClick={() => setSide("buy")}
              className={`px-4 py-1.5 rounded-md text-sm font-semibold transition-colors ${
                side === "buy" ? "bg-foreground text-background" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Buy
            </button>
            <button
              onClick={() => setSide("sell")}
              className={`px-4 py-1.5 rounded-md text-sm font-semibold transition-colors ${
                side === "sell" ? "bg-foreground text-background" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Sell
            </button>
          </div>
          <span className="text-sm font-medium text-muted-foreground">Market</span>
        </div>

        {/* Outcome Selector - Large Buttons */}
        <div className="grid grid-cols-2 gap-2">
          {outcomes.map((outcome) => {
            const isSelected = selectedOutcome === outcome.id
            const isMore = outcome.id === "more"
            return (
              <button
                key={outcome.id}
                onClick={() => setSelectedOutcome(outcome.id)}
                className={`p-3 rounded-lg text-center transition-all ${
                  isSelected
                    ? isMore
                      ? "bg-emerald-600 text-white ring-2 ring-emerald-700 ring-offset-2"
                      : "bg-red-500 text-white ring-2 ring-red-600 ring-offset-2"
                    : isMore
                    ? "bg-emerald-600 text-white opacity-60 hover:opacity-100"
                    : "bg-red-500 text-white opacity-60 hover:opacity-100"
                }`}
              >
                <div className="text-xs font-medium mb-1">{outcome.label}</div>
                <div className="text-xl font-bold">{(outcome.probability / 100).toFixed(2)}¢</div>
              </button>
            )
          })}
        </div>

        {/* Amount Input */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-semibold">Amount</label>
            <div className="text-3xl font-bold text-muted-foreground">${amount || "0"}</div>
          </div>
          <div className="grid grid-cols-4 gap-2">
            {presetAmounts.map((preset) => (
              <button
                key={preset}
                onClick={() => setAmount(preset.toString())}
                className="py-1.5 px-2 text-xs font-medium rounded border border-border hover:bg-accent"
              >
                +${preset}
              </button>
            ))}
            <button
              onClick={() => setAmount("")}
              className="py-1.5 px-2 text-xs font-medium rounded border border-border hover:bg-accent"
            >
              Max
            </button>
          </div>
        </div>

        {/* Trade Button */}
        <Button
          className="w-full bg-[#4F46E5] hover:bg-[#4338CA] text-white font-bold py-6 text-lg rounded-lg"
          size="lg"
        >
          Trade
        </Button>

        {/* Trade Summary - Below button */}
        {amount && parseFloat(amount) > 0 && (() => {
          const selectedOutcomeData = outcomes.find(o => o.id === selectedOutcome)
          const price = selectedOutcomeData ? selectedOutcomeData.probability / 100 : 0.5
          const shares = (parseFloat(amount) / price).toFixed(2)
          const avgPrice = (price * 100).toFixed(1)
          const potentialReturn = (parseFloat(shares) - parseFloat(amount)).toFixed(2)
          
          return (
            <div className="space-y-2 pt-4 border-t border-border">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Shares</span>
                <span className="font-semibold text-lg">{shares}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Avg price</span>
                <span className="font-semibold text-lg">{avgPrice}¢ ({price.toFixed(3)})</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Potential return</span>
                <span className="font-semibold text-lg text-green-600">${potentialReturn}</span>
              </div>
            </div>
          )
        })()}
      </div>
    </Card>
  )
}
