import { MarketChart } from "@/components/market-chart"
import { MarketOutcomes } from "@/components/market-outcomes"
import { MarketContext } from "@/components/market-context"
import { MarketComments } from "@/components/market-comments"
import { TradingPanel } from "@/components/trading-panel"
import { RelatedMarkets } from "@/components/related-markets"
import { UserBudget } from "@/components/user-budget"
import { getPlayerHeadshotUrlByName, getPlayerIdByName } from "@/lib/nhl"

function getApiBase() {
  const raw = (process.env.MARKET_BACKEND_API_BASE_URL || "").replace(/\/$/, "")
  if (!raw) return ""
  if (raw.startsWith("http://") || raw.startsWith("https://")) return raw
  return `https://${raw}`
}

type LandingData = { headshot?: string; featuredStats?: any }

async function landingData(landingUrl?: string | null): Promise<LandingData> {
  try {
    if (landingUrl) {
      const r = await fetch(landingUrl, { next: { revalidate: 86400 } })
      if (r.ok) {
        const j = await r.json()
        return { headshot: j?.headshot, featuredStats: j?.featuredStats }
      }
    }
  } catch {}
  return {}
}

function toStat(metric?: string, sub?: string): string {
  const s = (sub || metric || "").toString().toLowerCase()
  if (s.includes("goal")) return "Total Goals"
  if (s.includes("assist")) return "Total Assists"
  if (s.includes("pt") || s.includes("points") || s === "pts") return "Total Points"
  return sub || metric || ""
}

export default async function MarketDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const API_BASE = getApiBase()
  if (!API_BASE) {
    // minimal fallback if backend URL is missing
    return (
      <div className="min-h-screen bg-background"><main className="container mx-auto px-4 py-8 max-w-3xl"><div className="text-red-500 text-sm">Backend URL not configured. Set MARKET_BACKEND_API_BASE_URL.</div></main></div>
    )
  }

  // Fetch market
  const res = await fetch(`${API_BASE}/api/amm/markets/${id}`, { next: { revalidate: 5 } })
  if (!res.ok) {
    return (
      <div className="min-h-screen bg-background"><main className="container mx-auto px-4 py-8 max-w-3xl"><div className="text-red-500 text-sm">Market not found.</div></main></div>
    )
  }
  const m = await res.json()

  const stat = toStat(m.metric, m.sub_category)
  // If landing_url is missing, build it from known IDs mapping
  const fallbackLandingUrl = m.landing_url || (m.player_name && getPlayerIdByName(m.player_name) ? `https://api-web.nhle.com/v1/player/${getPlayerIdByName(m.player_name)}/landing` : undefined)
  const landing = await landingData(fallbackLandingUrl)
  const image = landing.headshot || (m.player_name ? await getPlayerHeadshotUrlByName(m.player_name) : null)
  const projectionLine = Number(m.threshold || 0)
  const yesP = Number.isFinite(Number(m?.prices?.yes)) ? Math.round(Number(m.prices.yes) * 100) : 50
  const noP = 100 - yesP
  const volumeLabel = m.volume_total ? `$${Number(m.volume_total).toLocaleString()}` : "$0"

  const marketData = {
    title: `${m.player_name || m.title} ${stat}`.trim(),
    subtitle: m.timeframe || "",
    image,
    volume: volumeLabel,
    ends: "",
    projectionLine,
    moreProbability: yesP,
    outcomes: [
      { id: "more", label: "Yes", probability: yesP, buyPrice: yesP, sellPrice: yesP, volume: volumeLabel },
      { id: "less", label: "No", probability: noP, buyPrice: noP, sellPrice: noP, volume: volumeLabel },
    ],
    relatedMarkets: [] as any[],
  }

  const fs = landing?.featuredStats?.regularSeason?.subSeason || landing?.featuredStats?.regularSeason || landing?.featuredStats || null

  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-3 sm:px-4 py-4 sm:py-6 md:py-8 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 md:gap-8">
          {/* Main Content - Left Side */}
          <div className="lg:col-span-2 space-y-4 sm:space-y-6">
            {/* Market Header */}
            <div className="flex items-start gap-3 sm:gap-4">
              <div className="w-24 h-24 sm:w-32 sm:h-32 rounded-lg overflow-hidden border-2 border-border/50 flex-shrink-0 bg-accent/30 flex items-center justify-center">
                {marketData.image ? (
                  <img src={marketData.image} alt="Player" className="w-full h-full object-cover" />
                ) : (
                  <span className="text-base sm:text-lg font-bold text-primary">
                    {(m.player_name || m.title || "?")
                      .toString()
                      .split(" ")
                      .slice(0, 2)
                      .map((n: string) => n[0])
                      .join("")}
                  </span>
                )}
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

            {/* Market Context with Featured Stats */}
            <MarketContext stats={fs} />

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
