import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface Outcome {
  id: string
  label: string
  probability: number
  buyPrice: number
  sellPrice: number
  volume: string
}

interface MarketOutcomesProps {
  outcomes: Outcome[]
  projectionLine?: number
}

export function MarketOutcomes({ outcomes, projectionLine = 60 }: MarketOutcomesProps) {
  return (
    <Card className="p-6">
      <div className="space-y-3">
        {outcomes.map((outcome) => (
          <div
            key={outcome.id}
            className="flex items-center justify-between gap-4 p-4 rounded-lg border border-border hover:bg-accent/30 transition-colors"
          >
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <h3 className="font-semibold text-lg">
                  {outcome.label === "Yes" ? "More" : "Less"} {projectionLine}
                </h3>
                <span className="text-2xl font-bold text-primary">${outcome.probability}IM</span>
              </div>
              <div className="text-sm text-muted-foreground">{outcome.volume} vol</div>
            </div>
            <div className="flex gap-2">
              <Button className="bg-green-600 hover:bg-green-700 text-white min-w-24">Buy ${outcome.buyPrice}IM</Button>
              <Button variant="outline" className="border-red-600 text-red-600 hover:bg-red-50 min-w-24 bg-transparent">
                Sell ${outcome.sellPrice}IM
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
