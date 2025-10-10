import Sidebar from "@/components/sidebar"
import InjuryReport from "@/components/injury-report"
import PlayerComparisonTool from "@/components/player-comparison-tool"
import PopularSearches from "@/components/popular-searches"
import FeaturedLinks from "@/components/featured-links"

export default function InjuriesPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        <Sidebar />
        <main className="flex-1">
          <div className="container mx-auto px-4 py-6">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <div className="lg:col-span-3">
                <InjuryReport />
              </div>
              <div className="space-y-6">
                <PlayerComparisonTool />
                <PopularSearches />
                <FeaturedLinks />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
