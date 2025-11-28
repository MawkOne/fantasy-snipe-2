import { ProjectionTile } from "@/components/projection-tile"
import { Search, SlidersHorizontal, Bookmark } from "lucide-react"

export default function ProjectionsPage() {
  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-6 max-w-7xl">
        <div className="mb-6">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search"
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
            Goals
          </button>
          <button className="px-4 py-2 rounded-lg bg-accent/50 text-muted-foreground font-medium whitespace-nowrap hover:bg-accent text-sm">
            Points
          </button>
          <button className="px-4 py-2 rounded-lg bg-accent/50 text-muted-foreground font-medium whitespace-nowrap hover:bg-accent text-sm">
            Assists
          </button>
          <button className="px-4 py-2 rounded-lg bg-accent/50 text-muted-foreground font-medium whitespace-nowrap hover:bg-accent text-sm">
            Goalies
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <ProjectionTile
            player="Connor McDavid"
            team="EDM"
            stat="Total Points"
            projectionLine={150.5}
            volume="$124.5K"
            category="Points"
          />
          <ProjectionTile
            player="Auston Matthews"
            team="TOR"
            stat="Total Goals"
            projectionLine={60.5}
            volume="$98.2K"
            category="Goals"
          />
          <ProjectionTile
            player="Nathan MacKinnon"
            team="COL"
            stat="Total Points"
            projectionLine={135.5}
            volume="$156.8K"
            category="Points"
          />
          <ProjectionTile
            player="David Pastrnak"
            team="BOS"
            stat="Total Goals"
            projectionLine={50.5}
            volume="$87.3K"
            category="Goals"
          />
          <ProjectionTile
            player="Cale Makar"
            team="COL"
            stat="Total Points"
            projectionLine={85.5}
            volume="$112.4K"
            category="Points"
          />
          <ProjectionTile
            player="Igor Shesterkin"
            team="NYR"
            stat="Save Percentage"
            projectionLine={0.92}
            volume="$76.9K"
            category="Goalies"
          />
          <ProjectionTile
            player="Leon Draisaitl"
            team="EDM"
            stat="Total Points"
            projectionLine={120.5}
            volume="$94.1K"
            category="Points"
          />
          <ProjectionTile
            player="Nikita Kucherov"
            team="TBL"
            stat="Total Assists"
            projectionLine={75.5}
            volume="$68.5K"
            category="Assists"
          />
          <ProjectionTile
            player="Connor Hellebuyck"
            team="WPG"
            stat="Total Wins"
            projectionLine={35.5}
            volume="$89.7K"
            category="Goalies"
          />
          <ProjectionTile
            player="Artemi Panarin"
            team="NYR"
            stat="Total Points"
            projectionLine={110.5}
            volume="$72.3K"
            category="Points"
          />
          <ProjectionTile
            player="Matthew Tkachuk"
            team="FLA"
            stat="Total Goals"
            projectionLine={45.5}
            volume="$81.6K"
            category="Goals"
          />
          <ProjectionTile
            player="Quinn Hughes"
            team="VAN"
            stat="Total Points"
            projectionLine={90.5}
            volume="$65.2K"
            category="Points"
          />
        </div>
      </main>
    </div>
  )
}
