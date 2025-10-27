"use client"

import { useState } from "react"
import { TradingPanel } from "./trading-panel"
import { RelatedMarkets } from "./related-markets"

interface Outcome {
  id: string
  label: string
  probability: number
  buyPrice: number
  sellPrice: number
}

interface TradingPanelWrapperProps {
  outcomes: Outcome[]
  relatedMarkets: any[]
}

export function TradingPanelWrapper({ outcomes, relatedMarkets }: TradingPanelWrapperProps) {
  const [amount, setAmount] = useState("")
  const [selectedOutcome, setSelectedOutcome] = useState(outcomes[0]?.id || "more")

  return (
    <>
      <TradingPanel 
        outcomes={outcomes} 
        amount={amount}
        setAmount={setAmount}
        selectedOutcome={selectedOutcome}
        setSelectedOutcome={setSelectedOutcome}
      />
      <RelatedMarkets markets={relatedMarkets} />
    </>
  )
}

