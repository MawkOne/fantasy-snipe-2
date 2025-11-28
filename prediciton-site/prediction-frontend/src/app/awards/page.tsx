import { MarketTile } from "@/components/market-tile"
import { Search, SlidersHorizontal, Bookmark } from "lucide-react"

export default function AwardsPage() {
  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-6">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search awards forecasts"
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
            Hart
          </button>
          <button className="px-4 py-2 rounded-lg bg-accent/50 text-muted-foreground font-medium whitespace-nowrap hover:bg-accent text-sm">
            Norris
          </button>
          <button className="px-4 py-2 rounded-lg bg-accent/50 text-muted-foreground font-medium whitespace-nowrap hover:bg-accent text-sm">
            Vezina
          </button>
          <button className="px-4 py-2 rounded-lg bg-accent/50 text-muted-foreground font-medium whitespace-nowrap hover:bg-accent text-sm">
            Calder
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <MarketTile
            title="Hart Trophy (MVP)"
            subtitle="Most Valuable Player"
            options={[
              { label: "Connor McDavid", probability: 45, team: "EDM" },
              { label: "Nathan MacKinnon", probability: 25, team: "COL" },
              { label: "Auston Matthews", probability: 15, team: "TOR" },
            ]}
            volume="$2.1M"
            category="Hart"
            marketId="hart-trophy"
            type="multi"
          />
          <MarketTile
            title="Norris Trophy"
            subtitle="Best Defenseman"
            options={[
              { label: "Cale Makar", probability: 50, team: "COL" },
              { label: "Quinn Hughes", probability: 20, team: "VAN" },
              { label: "Adam Fox", probability: 12, team: "NYR" },
            ]}
            volume="$1.4M"
            category="Norris"
            marketId="norris-trophy"
            type="multi"
          />
          <MarketTile
            title="Vezina Trophy"
            subtitle="Best Goaltender"
            options={[
              { label: "Connor Hellebuyck", probability: 30, team: "WPG" },
              { label: "Igor Shesterkin", probability: 25, team: "NYR" },
              { label: "Ilya Sorokin", probability: 18, team: "NYI" },
            ]}
            volume="$1.1M"
            category="Vezina"
            marketId="vezina-trophy"
            type="multi"
          />
          <MarketTile
            title="Calder Trophy"
            subtitle="Rookie of the Year"
            options={[
              { label: "Connor Bedard", probability: 55, team: "CHI" },
              { label: "Adam Fantilli", probability: 20, team: "CBJ" },
              { label: "Leo Carlsson", probability: 12, team: "ANA" },
            ]}
            volume="$890K"
            category="Calder"
            marketId="calder-trophy"
            type="multi"
          />
          <MarketTile
            title="Selke Trophy"
            subtitle="Best Defensive Forward"
            options={[
              { label: "Aleksander Barkov", probability: 35, team: "FLA" },
              { label: "Patrice Bergeron", probability: 25, team: "BOS" },
              { label: "Nico Hischier", probability: 15, team: "NJD" },
            ]}
            volume="$720K"
            category="Selke"
            marketId="selke-trophy"
            type="multi"
          />
          <MarketTile
            title="Jack Adams Award"
            subtitle="Coach of the Year"
            options={[
              { label: "Paul Maurice", probability: 28, team: "FLA" },
              { label: "Rod Brind'Amour", probability: 22, team: "CAR" },
              { label: "Jared Bednar", probability: 18, team: "COL" },
            ]}
            volume="$650K"
            category="Jack Adams"
            marketId="jack-adams-award"
            type="multi"
          />
        </div>
      </main>
    </div>
  )
}
