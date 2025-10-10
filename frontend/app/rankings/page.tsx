import Sidebar from "@/components/sidebar"
import RankingsTable from "@/components/rankings-table"
import RankingsFilters from "@/components/rankings-filters"
import VorpTable from "@/components/vorp-table"
import PlayerComparisonTool from "@/components/player-comparison-tool"
import PopularSearches from "@/components/popular-searches"
import FeaturedLinks from "@/components/featured-links"
import { Button } from "@/components/ui/button"

export default function RankingsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        <Sidebar />
        <main className="flex-1">
          <div className="container mx-auto px-4 py-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Fantasy Hockey Draft Rankings (2025)</h1>
                <p className="text-gray-600 mt-1">Consensus of 47 Experts (21 available) - Aug 5, 2025</p>
              </div>
              <div className="flex space-x-3">
                <Button className="bg-blue-600 hover:bg-blue-700">Pick Experts</Button>
                <Button variant="outline">Upgrade</Button>
              </div>
            </div>

            <RankingsFilters />

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <p className="text-blue-800 text-center">
                Sync your Cheat Sheet to your Draft for pick by pick advice {">>"}
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <div className="lg:col-span-3 space-y-6">
                <RankingsTable />
                <div>
                  <h2 className="text-xl font-semibold mb-2">VORP/PT Tiers (KMeans)</h2>
                  <VorpTable />
                </div>
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
