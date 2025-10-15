import { ProjectionSitesMarket } from "@/components/projection-sites-market"
import { ProjectionAccuracyGrid } from "@/components/projection-accuracy-grid"
import { MarketNavigation } from "@/components/market-navigation"

export default function ProjectionsMarketPage() {
  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <MarketNavigation activeTab="projections" />

        <div className="space-y-12">
          <ProjectionSitesMarket />
          <ProjectionAccuracyGrid />
        </div>
      </main>
    </div>
  )
}
