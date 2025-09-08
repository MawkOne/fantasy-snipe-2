import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Plus, Users, Clock, Trophy, Settings } from "lucide-react"

export default function DraftWizardDashboard() {
  const recentDrafts = [
    {
      id: 1,
      name: "My Hockey League 2025",
      type: "Snake Draft",
      teams: 12,
      status: "Completed",
      date: "Aug 3, 2025",
      grade: "A-",
    },
    {
      id: 2,
      name: "Friends & Family League",
      type: "Auction Draft",
      teams: 10,
      status: "In Progress",
      date: "Aug 4, 2025",
      grade: null,
    },
    {
      id: 3,
      name: "Work League Championship",
      type: "Snake Draft",
      teams: 14,
      status: "Scheduled",
      date: "Aug 6, 2025",
      grade: null,
    },
  ]

  const draftTemplates = [
    {
      name: "Standard League",
      description: "12 teams, snake draft, standard scoring",
      teams: 12,
      type: "Snake",
    },
    {
      name: "Points League",
      description: "10 teams, auction draft, points scoring",
      teams: 10,
      type: "Auction",
    },
    {
      name: "Dynasty League",
      description: "14 teams, snake draft, keeper format",
      teams: 14,
      type: "Snake",
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Completed":
        return "bg-green-100 text-green-800"
      case "In Progress":
        return "bg-blue-100 text-blue-800"
      case "Scheduled":
        return "bg-yellow-100 text-yellow-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Draft Wizard</h1>
        <p className="text-gray-600">AI-powered draft assistant for fantasy hockey</p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card className="hover:shadow-lg transition-shadow cursor-pointer">
          <CardContent className="p-6 text-center">
            <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
              <Plus className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="font-semibold text-lg mb-2">Start New Draft</h3>
            <p className="text-gray-600 text-sm mb-4">Create a new draft room with AI assistance</p>
            <Button className="w-full bg-blue-600 hover:bg-blue-700">Create Draft</Button>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow cursor-pointer">
          <CardContent className="p-6 text-center">
            <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
              <Users className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="font-semibold text-lg mb-2">Join Draft</h3>
            <p className="text-gray-600 text-sm mb-4">Enter an existing draft room</p>
            <Button variant="outline" className="w-full bg-transparent">
              Join Room
            </Button>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow cursor-pointer">
          <CardContent className="p-6 text-center">
            <div className="bg-purple-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
              <Trophy className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="font-semibold text-lg mb-2">Mock Draft</h3>
            <p className="text-gray-600 text-sm mb-4">Practice with AI opponents</p>
            <Button variant="outline" className="w-full bg-transparent">
              Start Mock
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Drafts */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Recent Drafts
              <Button variant="outline" size="sm">
                View All
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentDrafts.map((draft) => (
                <div key={draft.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900">{draft.name}</h4>
                    <div className="flex items-center space-x-2 text-sm text-gray-600 mt-1">
                      <span>{draft.type}</span>
                      <span>•</span>
                      <span>{draft.teams} teams</span>
                      <span>•</span>
                      <span>{draft.date}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {draft.grade && (
                      <Badge variant="outline" className="bg-green-50 text-green-700">
                        Grade: {draft.grade}
                      </Badge>
                    )}
                    <Badge className={getStatusColor(draft.status)}>{draft.status}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Draft Templates */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Start Templates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {draftTemplates.map((template, index) => (
                <div key={index} className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-900">{template.name}</h4>
                    <Button size="sm" variant="outline">
                      Use Template
                    </Button>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{template.description}</p>
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <span>{template.teams} Teams</span>
                    <span>{template.type} Draft</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI Features */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>AI-Powered Features</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="bg-blue-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                <Settings className="w-6 h-6 text-blue-600" />
              </div>
              <h4 className="font-semibold mb-2">Smart Recommendations</h4>
              <p className="text-sm text-gray-600">AI analyzes your team needs and suggests optimal picks</p>
            </div>
            <div className="text-center">
              <div className="bg-green-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                <Clock className="w-6 h-6 text-green-600" />
              </div>
              <h4 className="font-semibold mb-2">Real-time Analysis</h4>
              <p className="text-sm text-gray-600">Live draft grades and strategy adjustments</p>
            </div>
            <div className="text-center">
              <div className="bg-purple-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-3">
                <Trophy className="w-6 h-6 text-purple-600" />
              </div>
              <h4 className="font-semibold mb-2">Predictive Modeling</h4>
              <p className="text-sm text-gray-600">Advanced algorithms predict player performance</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
