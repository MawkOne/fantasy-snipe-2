import { Card } from "@/components/ui/card"

interface RelatedMarket {
  title: string
  probability: number
}

interface RelatedMarketsProps {
  markets: RelatedMarket[]
}

export function RelatedMarkets({ markets }: RelatedMarketsProps) {
  if (markets.length === 0) return null
  
  return (
    <Card className="p-4">
      <h3 className="font-semibold mb-4">Related Forecasts</h3>
      <div className="space-y-3">
        {markets.map((market, index) => (
          <button
            key={index}
            className="w-full text-left p-3 rounded-lg bg-accent/30 hover:bg-accent/50 transition-colors"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium text-balance">{market.title}</span>
              <span className="text-sm font-bold text-primary whitespace-nowrap">{market.probability}%</span>
            </div>
          </button>
        ))}
      </div>
    </Card>
  )
}
