import { Card } from "@/components/ui/card"
import Link from "next/link"
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
    const res = await fetch(`${API_BASE}/api/amm/markets`, { next: { revalidate: 300 } })
    if (!res.ok) return []
    return res.json()
  } catch (e) {
    console.error("Failed to fetch markets:", e)
    return []
  }
}

async function headshotFromLanding(landingUrl?: string | null, fallbackName?: string | null): Promise<{ headshot: string | null; position: string | null; teamLogoUrl: string | null; currentGoals: number; currentAssists: number; currentPoints: number }> {
  try {
    if (landingUrl) {
      const r = await fetch(landingUrl, { next: { revalidate: 1800 } }) // Cache for 30 minutes
      if (r.ok) {
        const j = await r.json()
        const headshot = j && typeof j.headshot === "string" ? (j.headshot as string) : null
        const position = (j?.position || j?.positionCode || j?.playerPosition || null) as string | null
        const teamLogoUrl = (j?.teamLogo || null) as string | null
        
        // Always use season totals for listing page (performance optimization)
        const currentGoals = Number(j?.featuredStats?.regularSeason?.subSeason?.goals || 0)
        const currentAssists = Number(j?.featuredStats?.regularSeason?.subSeason?.assists || 0)
        const currentPoints = Number(j?.featuredStats?.regularSeason?.subSeason?.points || 0)
        
        return { headshot, position, teamLogoUrl, currentGoals, currentAssists, currentPoints }
      }
    }
  } catch {}
  if (fallbackName) return { headshot: await getPlayerHeadshotUrlByName(fallbackName), position: null, teamLogoUrl: null, currentGoals: 0, currentAssists: 0, currentPoints: 0 }
  return { headshot: null, position: null, teamLogoUrl: null, currentGoals: 0, currentAssists: 0, currentPoints: 0 }
}

function toStat(sub: string | undefined): string {
  if (!sub) return "Season"
  const s = String(sub).toLowerCase()
  if (s.includes("goal")) return "Season Goals"
  if (s.includes("assist")) return "Season Assists"
  if (s.includes("pt") || s.includes("point")) return "Season Points"
  return sub
}

export default async function PlayersPage({ searchParams }: { searchParams?: Promise<Record<string, string>> }) {
  const [markets, base] = await Promise.all([fetchMarkets(), computeBlendedTop50()])
  const playerMkts = (markets || []).filter((m: any) => m.category === "Players")

  // Fetch headshots for the markets (best-effort)
  // Backend now provides timeframe_stats for Weekly/Monthly contracts
  let marketWithImages = await Promise.all(
    playerMkts.map(async (m: any) => {
      const info = await headshotFromLanding(m.landing_url, m.player_name)
      // Map NHL position codes to buckets
      const code = (info.position || "").toUpperCase()
      const posBucket = code === "G" ? "G" : code === "D" ? "D" : code ? "F" : null // C/LW/RW => F
      
      // Determine current stat based on metric
      const metric = (m.metric || "").toUpperCase()
      let currentStat = 0
      
      // Use timeframe_stats from backend if available (for Weekly/Monthly)
      if (m.timeframe_stats && (m.timeframe === "Weekly" || m.timeframe === "Monthly")) {
        currentStat = metric === "G" ? (m.timeframe_stats.goals || 0) : 
                      metric === "A" ? (m.timeframe_stats.assists || 0) : 
                      (m.timeframe_stats.points || 0)
      } else {
        // Use season totals from landing for Season contracts
        currentStat = metric === "G" ? info.currentGoals : metric === "A" ? info.currentAssists : info.currentPoints
      }
      
      const statLabel = metric === "G" ? "Goals" : metric === "A" ? "Ast" : "Pts"
      const statAbbrev = metric === "G" ? "G" : metric === "A" ? "A" : "Pts"
      return { ...m, imageUrl: info.headshot, teamLogoUrl: info.teamLogoUrl, pos: posBucket, currentStat, statLabel, statAbbrev, timeframe: m.timeframe }
    })
  )

  // Filter by metric (Points | Goals | Assists) if provided
  const sp = searchParams ? await searchParams : undefined
  const wanted = sp?.metric ? String(sp.metric) : undefined
  const wantedPos = sp?.pos ? String(sp.pos).toUpperCase() : undefined // F | D | G
  const wantedTimeframe = sp?.timeframe ? String(sp.timeframe) : undefined // Season | Monthly | Weekly
  const metricMap: Record<string, string> = { Points: "PTS", Goals: "G", Assists: "A" }
  if (wanted && wanted in metricMap) {
    marketWithImages = marketWithImages.filter((m: any) => (m.metric || "").toUpperCase() === metricMap[wanted])
  }

  // Apply position filter if provided
  if (wantedPos && ["F", "D", "G"].includes(wantedPos)) {
    marketWithImages = marketWithImages.filter((m: any) => (m.pos ? m.pos === wantedPos : true))
  }

  // Apply timeframe filter if provided
  if (wantedTimeframe && ["Season", "Monthly", "Weekly"].includes(wantedTimeframe)) {
    marketWithImages = marketWithImages.filter((m: any) => (m.timeframe || "").toLowerCase() === wantedTimeframe.toLowerCase())
  }

  // Sort by projection/threshold desc
  marketWithImages.sort((a: any, b: any) => Number(b?.threshold || 0) - Number(a?.threshold || 0))

  const players = await Promise.all(
    base.map(async (p: any) => ({ name: p.name, blended: p.blended, headshot: await getPlayerHeadshotUrlByName(p.name) }))
  )

  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 max-w-7xl">

        {API_BASE ? null : (
          <div className="mb-4 text-sm text-red-500">Backend URL not configured. Set MARKET_BACKEND_API_BASE_URL.</div>
        )}

        <div className="flex items-center justify-between gap-3 mb-6">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Sort by:</span>
            <select className="px-3 py-2 rounded-lg border border-border bg-background text-sm font-medium">
              <option value="points">Points</option>
              <option value="variance">Variance</option>
              <option value="name">Name</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Filter:</span>
            <select className="px-3 py-2 rounded-lg border border-border bg-background text-sm font-medium">
              <option value="all">All Markets</option>
              <option value="high-prob">High Probability (&gt;60%)</option>
              <option value="balanced">Balanced (40-60%)</option>
              <option value="low-prob">Low Probability (&lt;40%)</option>
            </select>
          </div>
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
              teamLogoUrl={m.teamLogoUrl}
              currentStat={m.currentStat}
              statLabel={m.statLabel}
              statAbbrev={m.statAbbrev}
              timeframe={m.timeframe}
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
