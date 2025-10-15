import { MarketTile } from "@/components/market-tile"
import { Search, SlidersHorizontal, Bookmark } from "lucide-react"

export default function HockeyMarketPage() {
  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-6">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search forecasts"
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
            Stanley Cup
          </button>
          <button className="px-4 py-2 rounded-lg bg-accent/50 text-muted-foreground font-medium whitespace-nowrap hover:bg-accent text-sm">
            Playoffs
          </button>
          <button className="px-4 py-2 rounded-lg bg-accent/50 text-muted-foreground font-medium whitespace-nowrap hover:bg-accent text-sm">
            Division
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <MarketTile
            title="Stanley Cup Champion"
            options={[
              { label: "Colorado Avalanche", probability: 18, team: "COL" },
              { label: "Florida Panthers", probability: 15, team: "FLA" },
              { label: "Edmonton Oilers", probability: 12, team: "EDM" },
            ]}
            volume="$2.4M"
            category="Championship"
            marketId="stanley-cup-champion"
            type="multi"
          />
          <MarketTile
            title="Eastern Conference Champion"
            options={[
              { label: "Florida Panthers", probability: 22, team: "FLA" },
              { label: "Carolina Hurricanes", probability: 18, team: "CAR" },
              { label: "New York Rangers", probability: 15, team: "NYR" },
            ]}
            volume="$1.8M"
            category="Playoffs"
            marketId="eastern-conference-champion"
            type="multi"
          />
          <MarketTile
            title="Western Conference Champion"
            options={[
              { label: "Colorado Avalanche", probability: 25, team: "COL" },
              { label: "Edmonton Oilers", probability: 20, team: "EDM" },
              { label: "Dallas Stars", probability: 15, team: "DAL" },
            ]}
            volume="$1.6M"
            category="Playoffs"
            marketId="western-conference-champion"
            type="multi"
          />
          <MarketTile
            title="Atlantic Division Winner"
            options={[
              { label: "Florida Panthers", probability: 35, team: "FLA" },
              { label: "Toronto Maple Leafs", probability: 28, team: "TOR" },
              { label: "Boston Bruins", probability: 20, team: "BOS" },
            ]}
            volume="$890K"
            category="Division"
            marketId="atlantic-division-winner"
            type="multi"
          />
          <MarketTile
            title="Metropolitan Division Winner"
            options={[
              { label: "Carolina Hurricanes", probability: 32, team: "CAR" },
              { label: "New York Rangers", probability: 28, team: "NYR" },
              { label: "New Jersey Devils", probability: 22, team: "NJD" },
            ]}
            volume="$765K"
            category="Division"
            marketId="metropolitan-division-winner"
            type="multi"
          />
          <MarketTile
            title="Central Division Winner"
            options={[
              { label: "Colorado Avalanche", probability: 38, team: "COL" },
              { label: "Dallas Stars", probability: 30, team: "DAL" },
              { label: "Winnipeg Jets", probability: 18, team: "WPG" },
            ]}
            volume="$820K"
            category="Division"
            marketId="central-division-winner"
            type="multi"
          />
          <MarketTile
            title="Pacific Division Winner"
            options={[
              { label: "Edmonton Oilers", probability: 35, team: "EDM" },
              { label: "Vegas Golden Knights", probability: 28, team: "VGK" },
              { label: "Los Angeles Kings", probability: 20, team: "LAK" },
            ]}
            volume="$710K"
            category="Division"
            marketId="pacific-division-winner"
            type="multi"
          />
        </div>
      </main>
    </div>
  )
}
