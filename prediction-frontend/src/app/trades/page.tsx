import { MarketTile } from "@/components/market-tile"
import { Search, SlidersHorizontal, Bookmark } from "lucide-react"

export default function TradesPage() {
  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-6">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search trade forecasts"
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
            Deadline
          </button>
          <button className="px-4 py-2 rounded-lg bg-accent/50 text-muted-foreground font-medium whitespace-nowrap hover:bg-accent text-sm">
            Offseason
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <MarketTile
            title="Elias Pettersson Traded?"
            subtitle="Before Trade Deadline"
            options={[
              { label: "Yes", probability: 35 },
              { label: "No", probability: 65 },
            ]}
            volume="$1.8M"
            category="Deadline"
            marketId="pettersson-traded"
            type="binary"
          />
          <MarketTile
            title="Mitch Marner Traded?"
            subtitle="Before Trade Deadline"
            options={[
              { label: "Yes", probability: 28 },
              { label: "No", probability: 72 },
            ]}
            volume="$1.5M"
            category="Deadline"
            marketId="marner-traded"
            type="binary"
          />
          <MarketTile
            title="Jakob Chychrun Next Team"
            options={[
              { label: "Toronto Maple Leafs", probability: 25, team: "TOR" },
              { label: "Los Angeles Kings", probability: 20, team: "LAK" },
              { label: "Carolina Hurricanes", probability: 18, team: "CAR" },
            ]}
            volume="$920K"
            category="Deadline"
            marketId="chychrun-next-team"
            type="multi"
          />
        </div>
      </main>
    </div>
  )
}
