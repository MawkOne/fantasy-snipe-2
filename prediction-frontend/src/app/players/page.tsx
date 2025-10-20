import { Card } from "@/components/ui/card"
import Link from "next/link"
import { Search } from "lucide-react"
import { computeBlendedTop50 } from "@/lib/blended"
import { getPlayerHeadshotUrlByName } from "@/lib/nhl"
import { ProjectionTile } from "@/components/projection-tile"

// Prefer Railway-provided MARKET_BACKEND_API_BASE_URL; add protocol if missing
function getApiBase() {
  const raw = (process.env.MARKET_BACKEND_API_BASE_URL || "").replace(/\/$/, "")
  if (!raw) return ""
  if (raw.startsWith("http://") || raw.startsWith("https://")) return raw
  return `https://${raw}`
}
const API_BASE = getApiBase()

async function fetchMarkets() {
  if (!API_BASE) return [] as any[]
  try {
    const res = await fetch(`${API_BASE}/api/amm/markets`, { next: { revalidate: 0 } })
    if (!res.ok) return []
    return res.json()
  } catch (e) {
    console.error("Failed to fetch markets:", e)
    return []
  }
}

async function headshotFromLanding(landingUrl?: string | null, fallbackName?: string | null): Promise<string | null> {
  try {
    if (landingUrl) {
      const r = await fetch(landingUrl, { next: { revalidate: 86400 } })
      if (r.ok) {
        const j = await r.json()
        if (j && typeof j.headshot === "string") return j.headshot as string
      }
    }
  } catch {}
  if (fallbackName) return getPlayerHeadshotUrlByName(fallbackName)
  return null
}

function toStat(sub: string | undefined): string {
  if (!sub) return "Total"
  const s = String(sub).toLowerCase()
  if (s.includes("goal")) return "Total Goals"
  if (s.includes("assist")) return "Total Assists"
  if (s.includes("pt") || s.includes("point")) return "Total Points"
  return sub
}

export default async function PlayersPage({ searchParams }: { searchParams?: Promise<Record<string, string>> }) {
  const [markets, base] = await Promise.all([fetchMarkets(), computeBlendedTop50()])
  const playerMkts = (markets || []).filter((m: any) => m.category === "Players")

  // Fetch headshots for the markets (best-effort)
  let marketWithImages = await Promise.all(
    playerMkts.map(async (m: any) => ({
      ...m,
      imageUrl: await headshotFromLanding(m.landing_url, m.player_name)
    }))
  )

  // Filter by metric (Points | Goals | Assists) if provided
  const sp = searchParams ? await searchParams : undefined
  const wanted = sp?.metric ? String(sp.metric) : undefined
  const metricMap: Record<string, string> = { Points: "PTS", Goals: "G", Assists: "A" }
  if (wanted && wanted in metricMap) {
    marketWithImages = marketWithImages.filter((m: any) => (m.metric || "").toUpperCase() === metricMap[wanted])
  }

  // Sort by projection/threshold desc
  marketWithImages.sort((a: any, b: any) => Number(b?.threshold || 0) - Number(a?.threshold || 0))

  const players = await Promise.all(
    base.map(async (p: any) => ({ name: p.name, blended: p.blended, headshot: await getPlayerHeadshotUrlByName(p.name) }))
  )

  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-6">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search players"
                className="w-full pl-10 pr-4 py-3 rounded-lg bg-accent/50 border border-border/50 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
          </div>
        </div>

        {API_BASE ? null : (
          <div className="mb-4 text-sm text-red-500">Backend URL not configured. Set MARKET_BACKEND_API_BASE_URL.</div>
        )}

        <div className="mb-2 text-sm text-muted-foreground">Active Player Contracts</div>
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2 scrollbar-hide">
          {[
            { label: "Points", q: "?metric=Points" },
            { label: "Goals", q: "?metric=Goals" },
            { label: "Assists", q: "?metric=Assists" },
          ].map(({ label, q }) => (
            <Link key={label} href={`/players${q}`} className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap text-sm ${wanted===label? 'bg-primary text-primary-foreground' : 'bg-accent/50 text-muted-foreground hover:bg-accent'}`}>
              {label}
            </Link>
          ))}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-10">
          {marketWithImages.map((m: any) => (
            <ProjectionTile
              key={m.id}
              player={m.player_name || m.title}
              team={m.team || ""}
              stat={toStat(m.sub_category)}
              projectionLine={Number.isFinite(Number(m.threshold)) ? Number(m.threshold) : 0}
              volume={`$${Number(m.volume_total || 0).toLocaleString()} Vol.`}
              category={m.sub_category || ""}
              yesProb={Number.isFinite(Number(m?.prices?.yes)) ? Number(m.prices.yes) * 100 : undefined}
              noProb={Number.isFinite(Number(m?.prices?.no)) ? Number(m.prices.no) * 100 : undefined}
              href={`/market/${m.id}`}
              imageUrl={m.imageUrl}
            />
          ))}
        </div>

        <div className="mb-4 text-sm text-muted-foreground">Top 50 blended projections</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {players.map((p: any, idx: number) => (
            <Card key={p.name} className="p-4 flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg overflow-hidden border border-border/50 flex-shrink-0 bg-accent/30">
                {p.headshot ? (
                  <img src={p.headshot} alt={p.name} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-sm text-muted-foreground">N/A</div>
                )}
              </div>
              <div className="min-w-0">
                <div className="font-semibold truncate">{idx + 1}. {p.name}</div>
                <div className="text-xs text-muted-foreground">Blended rank: {Math.round(p.blended)}</div>
              </div>
            </Card>
          ))}
        </div>
      </main>
    </div>
  )
}
