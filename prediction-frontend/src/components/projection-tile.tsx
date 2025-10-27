import { Card } from "@/components/ui/card"
import { Gift, Bookmark } from "lucide-react"
import Link from "next/link"

interface ProjectionTileProps {
  player: string
  team: string
  stat: string
  projectionLine: number
  volume: string
  category: string
  yesProb?: number // percentage 0-100
  noProb?: number  // percentage 0-100
  href?: string
  imageUrl?: string | null
  teamLogoUrl?: string | null
  currentStat?: number
  statLabel?: string
  statAbbrev?: string
  timeframe?: string
}

export function ProjectionTile({ player, team, stat, projectionLine, volume, category, yesProb, noProb, href, imageUrl, teamLogoUrl, currentStat, statLabel, statAbbrev, timeframe }: ProjectionTileProps) {
  const marketId = `${player.toLowerCase().replace(/\s+/g, "-")}-${stat.toLowerCase().replace(/\s+/g, "-")}`
  const link = href || `/market/${marketId}`
  const yesP = Number.isFinite(yesProb) ? Math.max(0, Math.min(100, Number(yesProb))) : 52
  const noP = Number.isFinite(noProb) ? Math.max(0, Math.min(100, Number(noProb))) : 48

  // Format timeframe label
  const getTimeframeLabel = () => {
    if (!timeframe) return ""
    
    if (timeframe === "Season") {
      return "Season"
    }
    
    if (timeframe === "Weekly") {
      // Calculate current week number (1-24) based on NHL season
      // Season started Sept 29, 2025 (Week 5 = Oct 27, 2025)
      const seasonStart = new Date("2025-09-29")
      const now = new Date()
      const diffTime = now.getTime() - seasonStart.getTime()
      const diffWeeks = Math.floor(diffTime / (1000 * 60 * 60 * 24 * 7)) + 1
      const weekNum = Math.max(1, Math.min(24, diffWeeks)) // Clamp between 1-24
      return `Week ${weekNum}`
    }
    
    if (timeframe === "Monthly") {
      // Get current month and year
      const now = new Date()
      const month = now.toLocaleDateString('en-US', { month: 'short' })
      const year = now.getFullYear().toString().slice(-2)
      return `${month} '${year}`
    }
    
    return timeframe
  }

  const timeframeLabel = getTimeframeLabel()

  return (
    <Link href={link}>
      <Card className="p-4 hover:bg-accent/30 transition-colors cursor-pointer border-border/50 bg-card/50">
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 rounded-lg overflow-hidden bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border border-border/50 flex-shrink-0">
              {imageUrl ? (
                <img src={imageUrl} alt={player} className="w-full h-full object-cover" />
              ) : (
                <span className="text-base font-bold text-primary">
                  {player
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-base text-foreground leading-tight">
                {player.split(' ').map((name, idx) => (
                  <div key={idx}>{name}</div>
                ))}
              </h3>
            </div>
            {currentStat !== undefined ? (
              <div className="ml-auto text-right">
                <div className="text-2xl font-bold text-foreground">
                  {currentStat} <span className="text-sm text-muted-foreground">{statLabel || "Current"}</span>
                </div>
              </div>
            ) : null}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-foreground">More {projectionLine} {statAbbrev}</span>
              <div className="flex items-center gap-2">
                <span className="text-lg font-semibold text-foreground min-w-[3rem] text-right">{yesP.toFixed(0)}%</span>
                <button className="w-12 py-0.5 rounded text-xs font-medium bg-emerald-500/15 hover:bg-emerald-500/25 transition-colors border border-emerald-500/30 text-emerald-600 dark:text-emerald-400">
                  More
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-foreground">Less {projectionLine} {statAbbrev}</span>
              <div className="flex items-center gap-2">
                <span className="text-lg font-semibold text-foreground min-w-[3rem] text-right">{noP.toFixed(0)}%</span>
                <button className="w-12 py-0.5 rounded text-xs font-medium bg-emerald-500/15 hover:bg-emerald-500/25 transition-colors border border-emerald-500/30 text-emerald-600 dark:text-emerald-400">
                  Less
                </button>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-border/50">
            {timeframeLabel && statAbbrev && (
              <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                timeframe === "Season" ? "bg-blue-500/15 text-blue-600 dark:text-blue-400" :
                timeframe === "Monthly" ? "bg-purple-500/15 text-purple-600 dark:text-purple-400" :
                "bg-orange-500/15 text-orange-600 dark:text-orange-400"
              }`}>
                {timeframeLabel} {timeframe === "Weekly" ? `Total ${statAbbrev}` : statAbbrev}
              </span>
            )}
            <div className="flex items-center gap-3">
              <button className="text-muted-foreground hover:text-foreground transition-colors">
                <Gift className="w-4 h-4" />
              </button>
              <button className="text-muted-foreground hover:text-foreground transition-colors">
                <Bookmark className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </Card>
    </Link>
  )
}
