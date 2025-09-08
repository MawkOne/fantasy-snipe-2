import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Check, Lock } from "lucide-react"

export default function PlaybookDashboard() {
  const features = [
    { name: "My Team", included: true },
    { name: "Top Available", included: true },
    { name: "Trade Central", included: true },
    { name: "Matchup", included: true },
    { name: "Cheat Sheets", included: true },
    { name: "10 Premium Tools", included: true, premium: true },
  ]

  const rosterPositions = [
    { position: "C", player: "", team: "", status: "" },
    { position: "C", player: "", team: "", status: "" },
    { position: "LW", player: "", team: "", status: "" },
    { position: "LW", player: "", team: "", status: "" },
    { position: "RW", player: "", team: "", status: "" },
    { position: "RW", player: "", team: "", status: "" },
    { position: "D", player: "", team: "", status: "" },
    { position: "D", player: "", team: "", status: "" },
    { position: "D", player: "", team: "", status: "" },
    { position: "D", player: "", team: "", status: "" },
    { position: "G", player: "", team: "", status: "" },
    { position: "G", player: "", team: "", status: "" },
    { position: "BN", player: "", team: "", status: "" },
    { position: "BN", player: "", team: "", status: "" },
    { position: "BN", player: "", team: "", status: "" },
    { position: "IR", player: "", team: "", status: "" },
  ]

  return (
    <div className="flex-1 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header Section */}
        <div className="text-center mb-12">
          <p className="text-blue-600 font-medium mb-4">The best in-season tools in the industry</p>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Dominate Your Fantasy League</h1>
          <p className="text-gray-600 text-lg mb-8 max-w-2xl mx-auto">
            Sync your league with My Playbook and get fast, FREE advice for your team from 100+ fantasy experts!
          </p>

          {/* Features Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8 max-w-2xl mx-auto">
            {features.map((feature) => (
              <div key={feature.name} className="flex items-center space-x-2">
                <Check className="w-5 h-5 text-green-600" />
                <span className="text-gray-700 flex items-center space-x-1">
                  <span>{feature.name}</span>
                  {feature.premium && <Lock className="w-3 h-3 text-orange-500" />}
                </span>
              </div>
            ))}
          </div>

          <a href="/sync">
            <Button size="lg" className="bg-blue-600 hover:bg-blue-700 px-8 py-3 text-lg">
              Sync Your League
            </Button>
          </a>
        </div>

        {/* Roster Preview */}
        <Card className="bg-gray-50">
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {rosterPositions.map((slot, index) => (
                <div key={index} className="flex items-center space-x-3 p-3 bg-white rounded-lg border border-gray-200">
                  <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                    <span className="text-xs font-semibold text-gray-600">{slot.position}</span>
                  </div>
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 rounded animate-pulse mb-1"></div>
                    <div className="h-3 bg-gray-100 rounded animate-pulse w-2/3"></div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 text-center">
              <p className="text-gray-500 mb-4">Connect your league to see your roster and get personalized advice</p>
              <a href="/sync">
                <Button variant="outline" className="border-blue-600 text-blue-600 hover:bg-blue-50 bg-transparent">
                  Connect League
                </Button>
              </a>
            </div>
          </CardContent>
        </Card>

        {/* Footer Links */}
        <div className="mt-16 pt-8 border-t border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-sm">
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">NHL</h4>
              <div className="space-y-2">
                <Link href="/nhl/rankings" className="block text-gray-600 hover:text-blue-600">
                  Rankings
                </Link>
                <Link href="/nhl/projections" className="block text-gray-600 hover:text-blue-600">
                  Projections
                </Link>
                <Link href="/nhl/draft" className="block text-gray-600 hover:text-blue-600">
                  Draft Tools
                </Link>
              </div>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Tools</h4>
              <div className="space-y-2">
                <Link href="/tools/trade-analyzer" className="block text-gray-600 hover:text-blue-600">
                  Trade Analyzer
                </Link>
                <Link href="/tools/waiver-wire" className="block text-gray-600 hover:text-blue-600">
                  Waiver Wire
                </Link>
                <Link href="/tools/lineup-optimizer" className="block text-gray-600 hover:text-blue-600">
                  Lineup Optimizer
                </Link>
              </div>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Premium</h4>
              <div className="space-y-2">
                <Link href="/premium" className="block text-gray-600 hover:text-blue-600">
                  Upgrade
                </Link>
                <Link href="/premium/features" className="block text-gray-600 hover:text-blue-600">
                  Premium Features
                </Link>
                <Link href="/premium/pricing" className="block text-gray-600 hover:text-blue-600">
                  Pricing
                </Link>
              </div>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Support</h4>
              <div className="space-y-2">
                <Link href="/help" className="block text-gray-600 hover:text-blue-600">
                  Help Center
                </Link>
                <Link href="/contact" className="block text-gray-600 hover:text-blue-600">
                  Contact Us
                </Link>
                <Link href="/mobile" className="block text-gray-600 hover:text-blue-600">
                  Mobile Apps
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
