import { Card } from "@/components/ui/card"
import { Gift, Bookmark } from "lucide-react"
import Link from "next/link"

interface MarketOption {
  label: string
  probability: number
  team?: string
}

interface MarketTileProps {
  title: string
  subtitle?: string
  image?: string
  options: MarketOption[]
  volume: string
  category: string
  marketId: string
  type: "binary" | "multi"
}

export function MarketTile({ title, subtitle, image, options, volume, category, marketId, type }: MarketTileProps) {
  const href = type === "binary" ? `/market/${marketId}` : `/market/multi/${marketId}`

  return (
    <Link href={href}>
      <Card className="p-4 hover:bg-accent/30 transition-colors cursor-pointer border-border/50 bg-card/50">
        <div className="space-y-3">
          {/* Header with image/icon and title */}
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border border-border/50 flex-shrink-0">
              {image ? (
                <img src={image || "/placeholder.svg"} alt={title} className="w-full h-full object-cover rounded-lg" />
              ) : (
                <span className="text-base font-bold text-primary">
                  {title
                    .split(" ")
                    .slice(0, 2)
                    .map((n) => n[0])
                    .join("")}
                </span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-base text-foreground leading-tight">{title}</h3>
              {subtitle && <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>}
            </div>
          </div>

          {/* Options */}
          <div className="space-y-2">
            {options.map((option, index) => (
              <div key={index} className="flex items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <span className="text-sm text-foreground">{option.label}</span>
                  {option.team && <span className="text-xs text-muted-foreground ml-1">({option.team})</span>}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-semibold text-foreground min-w-[3rem] text-right">
                    {option.probability}%
                  </span>
                  <button className="px-3 py-1.5 rounded bg-emerald-500/15 hover:bg-emerald-500/25 transition-colors border border-emerald-500/30 min-w-[3rem]">
                    <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">Yes</span>
                  </button>
                  <button className="px-3 py-1.5 rounded bg-rose-500/15 hover:bg-rose-500/25 transition-colors border border-rose-500/30 min-w-[3rem]">
                    <span className="text-xs font-medium text-rose-600 dark:text-rose-400">No</span>
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Footer with volume and actions */}
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
