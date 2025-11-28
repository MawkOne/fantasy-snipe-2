import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Star, ExternalLink } from "lucide-react"
import Image from "next/image"
import Link from "next/link"

export default function ResearchContent() {
  const newsItems = [
    {
      id: 1,
      headline: "Connor McDavid signs 8-year extension with Oilers",
      timestamp: "Mon, Aug 4th 6:15pm EDT",
      author: "FantasySnipe.ai Staff",
      category: "Contracts",
      playerImage: "/hockey-player-headshot.png",
      content:
        "The Edmonton Oilers have signed superstar center Connor McDavid to an 8-year, $100 million contract extension.",
      fantasyImpact:
        "McDavid remains the #1 fantasy pick across all formats. This extension ensures long-term stability and continued elite production in Edmonton's high-powered offense.",
      source: "ESPN Hockey",
    },
    {
      id: 2,
      headline: "Erik Karlsson traded to Pittsburgh Penguins",
      timestamp: "Mon, Aug 4th 5:45pm EDT",
      author: "FantasySnipe.ai Staff",
      category: "Transactions",
      playerImage: "/hockey-player-headshot.png",
      content:
        "The San Jose Sharks have traded defenseman Erik Karlsson to the Pittsburgh Penguins in a blockbuster deal.",
      fantasyImpact:
        "Karlsson's fantasy value gets a significant boost joining Pittsburgh's offense. Expect increased power-play opportunities and point production alongside Crosby and Malkin.",
      source: "TSN Hockey",
    },
    {
      id: 3,
      headline: "Igor Shesterkin placed on injured reserve",
      timestamp: "Mon, Aug 4th 4:30pm EDT",
      author: "FantasySnipe.ai Staff",
      category: "Injuries",
      playerImage: "/hockey-player-headshot.png",
      content:
        "New York Rangers goaltender Igor Shesterkin has been placed on injured reserve with a lower-body injury.",
      fantasyImpact:
        "Shesterkin owners should look for immediate replacement options. Jonathan Quick is expected to see increased starts while Shesterkin recovers.",
      source: "NHL.com",
    },
    {
      id: 4,
      headline: "Nathan MacKinnon returns from injury ahead of schedule",
      timestamp: "Mon, Aug 4th 3:20pm EDT",
      author: "FantasySnipe.ai Staff",
      category: "Injuries",
      playerImage: "/hockey-player-headshot.png",
      content:
        "Colorado Avalanche center Nathan MacKinnon is expected to return from his shoulder injury two weeks ahead of schedule.",
      fantasyImpact:
        "MacKinnon's early return is huge for fantasy managers. He should slot right back into the top line with Rantanen and maintain his elite scoring pace.",
      source: "The Athletic",
    },
    {
      id: 5,
      headline: "David Pastrnak signs with Boston Bruins",
      timestamp: "Mon, Aug 4th 2:10pm EDT",
      author: "FantasySnipe.ai Staff",
      category: "Contracts",
      playerImage: "/hockey-player-headshot.png",
      content:
        "The Boston Bruins have re-signed right winger David Pastrnak to a 8-year, $90 million contract extension.",
      fantasyImpact:
        "Pastrnak remains a top-5 fantasy winger with this deal. His goal-scoring ability and power-play production make him a must-have in all formats.",
      source: "Boston Globe",
    },
    {
      id: 6,
      headline: "Auston Matthews reaches 60-goal milestone",
      timestamp: "Mon, Aug 4th 1:00pm EDT",
      author: "FantasySnipe.ai Staff",
      category: "Performance",
      playerImage: "/hockey-player-headshot.png",
      content: "Toronto Maple Leafs center Auston Matthews has become the first player to reach 60 goals this season.",
      fantasyImpact:
        "Matthews continues to prove his elite fantasy value. His goal-scoring pace puts him in contention for the Rocket Richard Trophy and top fantasy scorer.",
      source: "Sportsnet",
    },
  ]

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "Transactions":
        return "bg-blue-100 text-blue-800"
      case "Injuries":
        return "bg-red-100 text-red-800"
      case "Contracts":
        return "bg-green-100 text-green-800"
      case "Performance":
        return "bg-purple-100 text-purple-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <div>
      {/* Header Section */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Fantasy Hockey News</h1>
            <p className="text-gray-600">Latest Player Updates</p>
          </div>
          <div className="flex items-center space-x-4">
            <Button variant="outline" size="sm" className="text-blue-600 border-blue-600 bg-transparent">
              Follow @FantasySnipeAI
            </Button>
            <Button variant="outline" size="sm" className="text-orange-600 border-orange-600 bg-transparent">
              <Star className="w-4 h-4 mr-1" />
              Join our News Desk
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4">
          <Select defaultValue="all-news">
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all-news">All News</SelectItem>
              <SelectItem value="transactions">Transactions</SelectItem>
              <SelectItem value="injuries">Injuries</SelectItem>
              <SelectItem value="contracts">Contracts</SelectItem>
              <SelectItem value="performance">Performance</SelectItem>
            </SelectContent>
          </Select>

          <Select defaultValue="all-teams">
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all-teams">All Teams</SelectItem>
              <SelectItem value="bos">Boston Bruins</SelectItem>
              <SelectItem value="col">Colorado Avalanche</SelectItem>
              <SelectItem value="edm">Edmonton Oilers</SelectItem>
              <SelectItem value="nyr">New York Rangers</SelectItem>
              <SelectItem value="pit">Pittsburgh Penguins</SelectItem>
              <SelectItem value="tor">Toronto Maple Leafs</SelectItem>
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
        </div>
      </div>

      {/* News Items */}
      <div className="space-y-6">
        {newsItems.map((item) => (
          <Card key={item.id} className="overflow-hidden hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex space-x-4">
                {/* Player Image */}
                <div className="flex-shrink-0">
                  <Image
                    src={item.playerImage || "/placeholder.svg"}
                    alt="Player"
                    width={80}
                    height={80}
                    className="rounded-lg object-cover"
                  />
                  <div className="mt-2 space-y-1">
                    <Link href="#" className="text-xs text-blue-600 hover:underline block">
                      + Rankings
                    </Link>
                    <Link href="#" className="text-xs text-blue-600 hover:underline block">
                      + Stats
                    </Link>
                    <Link href="#" className="text-xs text-blue-600 hover:underline block">
                      + More News
                    </Link>
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="mb-2">
                    <Link href={`/research/news/${item.id}`}>
                      <h2 className="text-xl font-bold text-blue-600 hover:text-blue-800 transition-colors">
                        {item.headline}
                      </h2>
                    </Link>
                    <div className="flex items-center space-x-2 text-sm text-gray-600 mt-1">
                      <span>{item.timestamp}</span>
                      <span>•</span>
                      <span>By {item.author}</span>
                    </div>
                  </div>

                  <div className="mb-4">
                    <p className="text-gray-700 mb-3">{item.content}</p>
                    <div className="bg-blue-50 border-l-4 border-blue-400 p-3 rounded">
                      <p className="text-sm">
                        <span className="font-semibold text-blue-900">Fantasy Impact:</span>{" "}
                        <span className="text-blue-800">{item.fantasyImpact}</span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">Category:</span>
                      <Badge className={getCategoryColor(item.category)}>{item.category}</Badge>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <span>Source: {item.source}</span>
                      <ExternalLink className="w-3 h-3" />
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Load More */}
      <div className="text-center mt-8">
        <Button variant="outline" size="lg">
          Load More News
        </Button>
      </div>
    </div>
  )
}
