import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { AlertTriangle, Clock, CheckCircle } from "lucide-react"
import Image from "next/image"

export default function InjuryReport() {
  const injuries = [
    {
      player: "Igor Shesterkin",
      team: "NYR",
      position: "G",
      injury: "Lower Body",
      status: "IR",
      timeline: "2-3 weeks",
      severity: "moderate",
      lastUpdate: "2 hours ago",
      image: "/hockey-player-headshot.png",
    },
    {
      player: "Frederik Andersen",
      team: "CAR",
      position: "G",
      injury: "Knee",
      status: "IR",
      timeline: "4-6 weeks",
      severity: "severe",
      lastUpdate: "1 day ago",
      image: "/hockey-player-headshot.png",
    },
    {
      player: "Kirill Kaprizov",
      team: "MIN",
      position: "LW",
      injury: "Upper Body",
      status: "Questionable",
      timeline: "Day-to-day",
      severity: "minor",
      lastUpdate: "3 hours ago",
      image: "/hockey-player-headshot.png",
    },
    {
      player: "Victor Hedman",
      team: "TBL",
      position: "D",
      injury: "Lower Body",
      status: "Probable",
      timeline: "Expected to play",
      severity: "minor",
      lastUpdate: "1 hour ago",
      image: "/hockey-player-headshot.png",
    },
    {
      player: "Brad Marchand",
      team: "BOS",
      position: "LW",
      injury: "Hip Surgery",
      status: "IR",
      timeline: "6-8 weeks",
      severity: "severe",
      lastUpdate: "5 days ago",
      image: "/hockey-player-headshot.png",
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "IR":
        return "bg-red-100 text-red-800"
      case "Questionable":
        return "bg-yellow-100 text-yellow-800"
      case "Probable":
        return "bg-green-100 text-green-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "severe":
        return <AlertTriangle className="w-4 h-4 text-red-600" />
      case "moderate":
        return <Clock className="w-4 h-4 text-yellow-600" />
      case "minor":
        return <CheckCircle className="w-4 h-4 text-green-600" />
      default:
        return <Clock className="w-4 h-4 text-gray-600" />
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Injury Report</h1>
        <p className="text-gray-600">Stay updated on player injuries and return timelines</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <Select defaultValue="all-teams">
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-teams">All Teams</SelectItem>
            <SelectItem value="bos">Boston Bruins</SelectItem>
            <SelectItem value="car">Carolina Hurricanes</SelectItem>
            <SelectItem value="min">Minnesota Wild</SelectItem>
            <SelectItem value="nyr">New York Rangers</SelectItem>
            <SelectItem value="tbl">Tampa Bay Lightning</SelectItem>
          </SelectContent>
        </Select>

        <Select defaultValue="all-positions">
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-positions">All Positions</SelectItem>
            <SelectItem value="c">Center</SelectItem>
            <SelectItem value="lw">Left Wing</SelectItem>
            <SelectItem value="rw">Right Wing</SelectItem>
            <SelectItem value="d">Defense</SelectItem>
            <SelectItem value="g">Goalie</SelectItem>
          </SelectContent>
        </Select>

        <Select defaultValue="all-status">
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-status">All Status</SelectItem>
            <SelectItem value="ir">Injured Reserve</SelectItem>
            <SelectItem value="questionable">Questionable</SelectItem>
            <SelectItem value="probable">Probable</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Injury List */}
      <Card>
        <CardHeader>
          <CardTitle>Current Injuries</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {injuries.map((injury, index) => (
              <div key={index} className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
                <Image
                  src={injury.image || "/placeholder.svg"}
                  alt={injury.player}
                  width={60}
                  height={60}
                  className="rounded-lg object-cover"
                />

                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <h3 className="font-semibold text-lg">{injury.player}</h3>
                    <Badge variant="outline">{injury.team}</Badge>
                    <Badge variant="outline">{injury.position}</Badge>
                  </div>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>Injury: {injury.injury}</span>
                    <span>•</span>
                    <span>Updated: {injury.lastUpdate}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-center">
                    <Badge className={getStatusColor(injury.status)}>{injury.status}</Badge>
                    <p className="text-xs text-gray-600 mt-1">{injury.timeline}</p>
                  </div>
                  {getSeverityIcon(injury.severity)}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* AI Insights */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>AI Injury Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-2">Recommended Pickups</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Jonathan Quick (NYR) - Shesterkin replacement</li>
                <li>• Antti Raanta (CAR) - Andersen backup</li>
                <li>• Matt Boldy (MIN) - Kaprizov's linemate</li>
              </ul>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg">
              <h4 className="font-semibold text-yellow-900 mb-2">Players to Monitor</h4>
              <ul className="text-sm text-yellow-800 space-y-1">
                <li>• Kaprizov expected back this week</li>
                <li>• Hedman likely to play next game</li>
                <li>• Marchand targeting return in 4-5 weeks</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
