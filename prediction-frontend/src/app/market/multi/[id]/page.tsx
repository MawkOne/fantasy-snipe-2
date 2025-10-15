import { MultiOptionChart } from "@/components/multi-option-chart"
import { MultiOptionOutcomes } from "@/components/multi-option-outcomes"
import { MarketContext } from "@/components/market-context"
import { MarketComments } from "@/components/market-comments"
import { TradingPanel } from "@/components/trading-panel"
import { RelatedMarkets } from "@/components/related-markets"
import { UserBudget } from "@/components/user-budget"
import { getPlayerHeadshotUrlByName } from "@/lib/nhl"

export default async function MultiOptionMarketPage() {
  const marketData = {
    title: "Hart Trophy Winner 2024-25",
    subtitle: "NHL Most Valuable Player",
    image: "/nhl-hart-trophy.jpg",
    volume: "$1.2M",
    ends: "Jun 30, 2025",
    outcomes: [
      {
        id: "mcdavid",
        name: "Connor McDavid",
        team: "EDM",
        probability: 45,
        buyPrice: 45,
        sellPrice: 47,
        volume: "$540K",
        image: await getPlayerHeadshotUrlByName("Connor McDavid"),
      },
      {
        id: "mackinnon",
        name: "Nathan MacKinnon",
        team: "COL",
        probability: 25,
        buyPrice: 25,
        sellPrice: 27,
        volume: "$300K",
        image: await getPlayerHeadshotUrlByName("Nathan MacKinnon"),
      },
      {
        id: "matthews",
        name: "Auston Matthews",
        team: "TOR",
        probability: 15,
        buyPrice: 15,
        sellPrice: 17,
        volume: "$180K",
        image: await getPlayerHeadshotUrlByName("Auston Matthews"),
      },
      {
        id: "kucherov",
        name: "Nikita Kucherov",
        team: "TBL",
        probability: 8,
        buyPrice: 8,
        sellPrice: 10,
        volume: "$96K",
        image: await getPlayerHeadshotUrlByName("Nikita Kucherov"),
      },
      {
        id: "draisaitl",
        name: "Leon Draisaitl",
        team: "EDM",
        probability: 5,
        buyPrice: 5,
        sellPrice: 7,
        volume: "$60K",
        image: await getPlayerHeadshotUrlByName("Leon Draisaitl"),
      },
      {
        id: "other",
        name: "Other",
        team: "",
        probability: 2,
        buyPrice: 2,
        sellPrice: 4,
        volume: "$24K",
        image: "",
      },
    ],
    relatedMarkets: [
      { title: "McDavid Total Points: More/Less 150.5", probability: 45 },
      { title: "Norris Trophy Winner", probability: 38 },
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
              <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-lg overflow-hidden border-2 border-border/50 flex-shrink-0 bg-gradient-to-br from-primary/20 to-primary/5">
                <img src={marketData.image || "/placeholder.svg"} alt="Market" className="w-full h-full object-cover" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold text-primary mb-1">MULTI-OPTION FORECAST</div>
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
            <MultiOptionChart outcomes={marketData.outcomes} />

            {/* Outcomes */}
            <MultiOptionOutcomes outcomes={marketData.outcomes} />

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
