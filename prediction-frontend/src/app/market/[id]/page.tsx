import { MarketChart } from "@/components/market-chart"
import { MarketOutcomes } from "@/components/market-outcomes"
import { MarketContext } from "@/components/market-context"
import { MarketComments } from "@/components/market-comments"
import { TradingPanel } from "@/components/trading-panel"
import { RelatedMarkets } from "@/components/related-markets"
import { UserBudget } from "@/components/user-budget"
import { getPlayerHeadshotUrlByName } from "@/lib/nhl"

export default async function MarketDetailPage() {
  const marketData = {
    title: "Connor McDavid Total Goals",
    subtitle: "2024-25 Regular Season",
    image: await getPlayerHeadshotUrlByName("Connor McDavid"),
    volume: "$234.5K",
    ends: "Apr 18, 2025",
    projectionLine: 60,
    moreProbability: 34,
    outcomes: [
      { id: "more", label: "Yes", probability: 34, buyPrice: 34, sellPrice: 36, volume: "$156.2K" },
      { id: "less", label: "No", probability: 66, buyPrice: 64, sellPrice: 66, volume: "$78.3K" },
    ],
    relatedMarkets: [
      { title: "McDavid Total Points: More/Less 150.5", probability: 45 },
      { title: "McDavid Hart Trophy Winner", probability: 38 },
      { title: "Oilers Stanley Cup Winner", probability: 12 },
    ],
  }

  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-3 sm:px-4 py-4 sm:py-6 md:py-8 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 md:gap-8">
          {/* Main Content - Left Side */}
          <div className="lg:col-span-2 space-y-4 sm:space-y-6">
            {/* Market Header */}
            <div className="flex items-start gap-3 sm:gap-4">
              <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-lg overflow-hidden border-2 border-border/50 flex-shrink-0">
                <img src={marketData.image || "/placeholder.svg"} alt="Player" className="w-full h-full object-cover" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold text-primary mb-1">PLAYER FORECAST</div>
                <h1 className="text-xl sm:text-2xl md:text-3xl font-bold mb-1 text-balance">{marketData.title}</h1>
                <p className="text-sm sm:text-base md:text-lg text-muted-foreground mb-2">{marketData.subtitle}</p>
                <div className="flex items-center gap-2 sm:gap-4 text-xs sm:text-sm text-muted-foreground flex-wrap">
                  <span>{marketData.volume} volume</span>
                  <span>•</span>
                  <span>Ends {marketData.ends}</span>
                </div>
              </div>
            </div>

            {/* Chart */}
            <MarketChart projectionLine={marketData.projectionLine} moreProbability={marketData.moreProbability} />

            {/* Outcomes */}
            <MarketOutcomes outcomes={marketData.outcomes} projectionLine={marketData.projectionLine} />

            {/* Market Context */}
            <MarketContext />

            {/* Comments */}
            <MarketComments />
          </div>

          {/* Trading Panel - Right Side */}
          <div className="lg:col-span-1">
            <div className="lg:sticky lg:top-8 space-y-4 sm:space-y-6">
              <UserBudget />
              <TradingPanel outcomes={marketData.outcomes} />
              <RelatedMarkets markets={marketData.relatedMarkets} />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
