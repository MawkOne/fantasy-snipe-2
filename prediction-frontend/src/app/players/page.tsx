import { Card } from "@/components/ui/card"
import { Search } from "lucide-react"
import { computeBlendedTop50 } from "@/lib/blended"
import { getPlayerHeadshotUrlByName } from "@/lib/nhl"

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || "").replace(/\/$/, "")

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

export default async function PlayersPage() {
  const [markets, base] = await Promise.all([fetchMarkets(), computeBlendedTop50()])
  const playerMkts = (markets || []).filter((m: any) => m.category === "Players")

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
          <div className="mb-4 text-sm text-red-500">Backend URL not configured. Set NEXT_PUBLIC_API_BASE.</div>
        )}

        <div className="mb-4 text-sm text-muted-foreground">Active Player Contracts</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-10">
          {playerMkts.map((m: any) => (
            <Card key={m.id} className="p-4">
              <div className="text-sm text-muted-foreground">{m.sub_category} · {m.timeframe}</div>
              <div className="font-semibold mt-1">{m.player_name || m.title}</div>
              {m.threshold != null && (
                <div className="text-xs text-muted-foreground">Line: {Number(m.threshold).toFixed(1)}</div>
              )}
              {m.prices && (
                <div className="text-xs mt-2">Yes {(m.prices.yes*100).toFixed(1)}% · No {(m.prices.no*100).toFixed(1)}%</div>
              )}
            </Card>
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
