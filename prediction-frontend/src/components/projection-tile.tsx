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
}

export function ProjectionTile({ player, team, stat, projectionLine, volume, category, yesProb, noProb, href, imageUrl, teamLogoUrl }: ProjectionTileProps) {
  const marketId = `${player.toLowerCase().replace(/\s+/g, "-")}-${stat.toLowerCase().replace(/\s+/g, "-")}`
  const link = href || `/market/${marketId}`
  const yesP = Number.isFinite(yesProb) ? Math.max(0, Math.min(100, Number(yesProb))) : 52
  const noP = Number.isFinite(noProb) ? Math.max(0, Math.min(100, Number(noProb))) : 48

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
              <h3 className="font-semibold text-base text-foreground leading-tight">{player}</h3>
              <div className="text-xs text-muted-foreground mt-0.5">{stat}</div>
            </div>
            {teamLogoUrl ? (
              <div className="ml-auto">
                <img src={teamLogoUrl} alt={team || 'team'} className="w-6 h-6 object-contain opacity-80" />
              </div>
            ) : null}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-foreground">More {projectionLine}</span>
              <div className="flex items-center gap-2">
                <span className="text-lg font-semibold text-foreground min-w-[3rem] text-right">{yesP.toFixed(0)}%</span>
                <button className="px-3 py-1.5 rounded bg-emerald-500/15 hover:bg-emerald-500/25 transition-colors border border-emerald-500/30 min-w-[3rem]">
                  <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">More</span>
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-foreground">Less {projectionLine}</span>
              <div className="flex items-center gap-2">
                <span className="text-lg font-semibold text-foreground min-w-[3rem] text-right">{noP.toFixed(0)}%</span>
                <button className="px-3 py-1.5 rounded bg-emerald-500/15 hover:bg-emerald-500/25 transition-colors border border-emerald-500/30 min-w-[3rem]">
                  <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">Less</span>
                </button>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-border/50">
            <span className="text-xs text-muted-foreground">{volume} Vol.</span>
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
