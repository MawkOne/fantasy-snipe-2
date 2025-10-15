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
}

export function ProjectionTile({ player, team, stat, projectionLine, volume, category }: ProjectionTileProps) {
  const marketId = `${player.toLowerCase().replace(/\s+/g, "-")}-${stat.toLowerCase().replace(/\s+/g, "-")}`

  return (
    <Link href={`/market/${marketId}`}>
      <Card className="p-4 hover:bg-accent/30 transition-colors cursor-pointer border-border/50 bg-card/50">
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border border-border/50 flex-shrink-0">
              <span className="text-base font-bold text-primary">
                {player
                  .split(" ")
                  .map((n) => n[0])
                  .join("")}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-base text-foreground leading-tight">{stat}</h3>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-foreground">More {projectionLine}</span>
              <div className="flex items-center gap-2">
                <span className="text-lg font-semibold text-foreground min-w-[3rem] text-right">52%</span>
                <button className="px-3 py-1.5 rounded bg-emerald-500/15 hover:bg-emerald-500/25 transition-colors border border-emerald-500/30 min-w-[3rem]">
                  <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">Yes</span>
                </button>
                <button className="px-3 py-1.5 rounded bg-rose-500/15 hover:bg-rose-500/25 transition-colors border border-rose-500/30 min-w-[3rem]">
                  <span className="text-xs font-medium text-rose-600 dark:text-rose-400">No</span>
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-foreground">Less {projectionLine}</span>
              <div className="flex items-center gap-2">
                <span className="text-lg font-semibold text-foreground min-w-[3rem] text-right">48%</span>
                <button className="px-3 py-1.5 rounded bg-emerald-500/15 hover:bg-emerald-500/25 transition-colors border border-emerald-500/30 min-w-[3rem]">
                  <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">Yes</span>
                </button>
                <button className="px-3 py-1.5 rounded bg-rose-500/15 hover:bg-rose-500/25 transition-colors border border-rose-500/30 min-w-[3rem]">
                  <span className="text-xs font-medium text-rose-600 dark:text-rose-400">No</span>
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
