import { MarketTile } from "@/components/market-tile"
import { Search, SlidersHorizontal, Bookmark } from "lucide-react"

export default function DraftPage() {
  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-6">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search draft forecasts"
                className="w-full pl-10 pr-4 py-3 rounded-lg bg-accent/50 border border-border/50 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
            <button className="p-3 rounded-lg bg-accent/50 border border-border/50 hover:bg-accent transition-colors">
              <SlidersHorizontal className="w-5 h-5 text-foreground" />
            </button>
            <button className="p-3 rounded-lg bg-accent/50 border border-border/50 hover:bg-accent transition-colors">
              <Bookmark className="w-5 h-5 text-foreground" />
            </button>
          </div>
        </div>

        <div className="flex gap-2 mb-6 overflow-x-auto pb-2 scrollbar-hide">
          <button className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-medium whitespace-nowrap text-sm">
            All
          </button>
          <button className="px-4 py-2 rounded-lg bg-accent/50 text-muted-foreground font-medium whitespace-nowrap hover:bg-accent text-sm">
            First Overall
          </button>
          <button className="px-4 py-2 rounded-lg bg-accent/50 text-muted-foreground font-medium whitespace-nowrap hover:bg-accent text-sm">
            Top 5
          </button>
          <button className="px-4 py-2 rounded-lg bg-accent/50 text-muted-foreground font-medium whitespace-nowrap hover:bg-accent text-sm">
            Top 10
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <MarketTile
            title="2025 First Overall Pick"
            options={[
              { label: "James Hagens", probability: 45 },
              { label: "Porter Martone", probability: 30 },
              { label: "Matthew Schaefer", probability: 15 },
            ]}
            volume="$1.3M"
            category="First Overall"
            marketId="first-overall-pick-2025"
            type="multi"
          />
          <MarketTile
            title="Top 5 Pick - Anton Frondell"
            subtitle="Will he go in the top 5?"
            options={[
              { label: "Yes", probability: 62 },
              { label: "No", probability: 38 },
            ]}
            volume="$780K"
            category="Top 5"
            marketId="frondell-top-5"
            type="binary"
          />
          <MarketTile
            title="First Goalie Selected"
            options={[
              { label: "Mikhail Yegorov", probability: 55 },
              { label: "Jack Ivankovic", probability: 25 },
              { label: "Luka Radivojevic", probability: 12 },
            ]}
            volume="$650K"
            category="Draft"
            marketId="first-goalie-selected"
            type="multi"
          />
        </div>
      </main>
    </div>
  )
}
