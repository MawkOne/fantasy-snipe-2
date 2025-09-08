import { Star } from "lucide-react"

export default function MyTeamContent() {
  const roster = [
    {
      position: "QB",
      positionColor: "bg-red-600",
      player: "Joe Burrow",
      team: "CIN",
      bye: 10,
      ecr: "QB 5",
      opponent: "@CLE",
      gameTime: "Sun 1:00 pm",
      matchupRating: 4,
      news: "Last year, Joe Burrow was the QB3 in fantasy points per game, fin...",
      avatar: "/joe-burrow-headshot.png",
    },
    {
      position: "RB",
      positionColor: "bg-green-600",
      player: "De'Von Achane",
      team: "MIA",
      bye: 12,
      ecr: "RB 5",
      opponent: "@IND",
      gameTime: "Sun 1:00 pm",
      matchupRating: 3,
      news: "Achane continued his strong RB1 ways last year as the RB6 in fant...",
      avatar: "/devon-achane-headshot.png",
    },
    {
      position: "RB",
      positionColor: "bg-green-600",
      player: "Derrick Henry",
      team: "BAL",
      bye: 7,
      ecr: "RB 7",
      opponent: "@BUF",
      gameTime: "Sun 8:20 pm",
      matchupRating: 4,
      news: "The BIG DAWG KEEPS EATING! Some players are just built different....",
      avatar: "/derrick-henry-headshot.png",
    },
    {
      position: "RB",
      positionColor: "bg-green-600",
      player: "D'Andre Swift",
      team: "CHI",
      bye: 5,
      ecr: "RB 22",
      opponent: "MIN",
      gameTime: "Mon 8:15 pm",
      matchupRating: 2,
      news: "Well, the Bears didn't add any threat to Swift's workload before ...",
      avatar: "/dandre-swift-headshot.png",
    },
    {
      position: "RB",
      positionColor: "bg-green-600",
      player: "Jaylen Warren",
      team: "PIT",
      bye: 5,
      ecr: "RB 30",
      opponent: "@NYJ",
      gameTime: "Sun 1:00 pm",
      matchupRating: 3,
      news: "After Warren's RB29 finish in 2023, I hoped he would take another...",
      avatar: "/jaylen-warren-headshot.png",
    },
    {
      position: "RB",
      positionColor: "bg-green-600",
      player: "Rachaad White",
      team: "TB",
      bye: 9,
      ecr: "RB 40",
      opponent: "@ATL",
      gameTime: "Sun 1:00 pm",
      matchupRating: 3,
      news: "Rachaad White (groin) now considered day-to-day »",
      avatar: "/rachaad-white-headshot.png",
    },
    {
      position: "WR",
      positionColor: "bg-blue-600",
      player: "Justin Jefferson",
      team: "MIN",
      bye: 6,
      ecr: "WR 3",
      opponent: "@CHI",
      gameTime: "Mon 8:15 pm",
      matchupRating: 3,
      news: "Jefferson has been the model of consistency. He has never finishe...",
      avatar: "/justin-jefferson-headshot.png",
    },
    {
      position: "WR",
      positionColor: "bg-blue-600",
      player: "Malik Nabers",
      team: "NYG",
      bye: 14,
      ecr: "WR 4",
      opponent: "@WAS",
      gameTime: "Sun 1:00 pm",
      matchupRating: 2,
      news: "Malik Nabers exploded in his rookie season as the WR7 in fantasy ...",
      avatar: "/malik-nabers-headshot.png",
    },
    {
      position: "WR",
      positionColor: "bg-blue-600",
      player: "Courtland Sutton",
      team: "DEN",
      bye: 12,
      ecr: "WR 22",
      opponent: "TEN",
      gameTime: "Sun 4:05 pm",
      matchupRating: 3,
      news: "As Bo Nix's WR1 last year, Courtland Sutton finished as the WR24 ...",
      avatar: "/courtland-sutton-headshot.png",
    },
    {
      position: "WR",
      positionColor: "bg-blue-600",
      player: "Michael Wilson",
      team: "ARI",
      bye: 8,
      ecr: "WR 75",
      opponent: "@NO",
      gameTime: "Sun 1:00 pm",
      matchupRating: 2,
      news: "Michael Wilson (concussion) misses practice Saturday »",
      avatar: "/michael-wilson-headshot.png",
    },
    {
      position: "TE",
      positionColor: "bg-yellow-600",
      player: "George Kittle",
      team: "SF",
      bye: 14,
      ecr: "TE 3",
      opponent: "@SEA",
      gameTime: "Sun 4:05 pm",
      matchupRating: 4,
      news: "Kittle remains an elite option at the tight end position and does...",
      avatar: "/placeholder.svg?height=40&width=40",
    },
    {
      position: "TE",
      positionColor: "bg-yellow-600",
      player: "Evan Engram",
      team: "DEN",
      bye: 12,
      ecr: "TE 7",
      opponent: "TEN",
      gameTime: "Sun 4:05 pm",
      matchupRating: 4,
      news: "Evan Engram could SMASH his ADP this year as Sean Payton's Joker....",
      avatar: "/placeholder.svg?height=40&width=40",
    },
    {
      position: "IDP",
      positionColor: "bg-purple-600",
      player: "Roquan Smith",
      team: "BAL",
      bye: 7,
      ecr: "IDP 2",
      opponent: "@BUF",
      gameTime: "Sun 8:20 pm",
      matchupRating: 0,
      news: "",
      avatar: "/placeholder.svg?height=40&width=40",
    },
    {
      position: "IDP",
      positionColor: "bg-purple-600",
      player: "Fred Warner",
      team: "SF",
      bye: 14,
      ecr: "IDP 3",
      opponent: "@SEA",
      gameTime: "Sun 4:05 pm",
      matchupRating: 0,
      news: "",
      avatar: "/placeholder.svg?height=40&width=40",
    },
    {
      position: "IDP",
      positionColor: "bg-purple-600",
      player: "Myles Garrett",
      team: "CLE",
      bye: 9,
      ecr: "IDP 6",
      opponent: "CIN",
      gameTime: "Sun 1:00 pm",
      matchupRating: 0,
      news: "Myles Garrett held out for precautionary rest »",
      avatar: "/placeholder.svg?height=40&width=40",
    },
  ]

  const renderStars = (rating: number) => {
    if (rating === 0) return <span className="text-gray-400">-</span>

    return (
      <div className="flex">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star key={star} className={`w-4 h-4 ${star <= rating ? "fill-blue-500 text-blue-500" : "text-gray-300"}`} />
        ))}
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">My Team</h1>
        <p className="text-gray-600">Manage your roster and get AI-powered insights</p>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">POS</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  PLAYER
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ECR</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  OPPONENT
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  MATCHUP
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  NEWS / NOTES
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {roster.map((player, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-4">
                    <div className="flex items-center">
                      <div className={`w-1 h-12 ${player.positionColor} rounded-r mr-3`}></div>
                      <span className="text-sm font-medium text-gray-900">{player.position}</span>
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-center">
                      <img
                        className="h-10 w-10 rounded-full mr-3"
                        src={player.avatar || "/placeholder.svg"}
                        alt={player.player}
                      />
                      <div>
                        <div className="text-sm font-medium text-blue-600 hover:text-blue-800 cursor-pointer">
                          {player.player}
                        </div>
                        <div className="text-sm text-gray-500">
                          ({player.team} - BYE: {player.bye})
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-900">{player.ecr}</td>
                  <td className="px-4 py-4">
                    <div className="text-sm text-gray-900">{player.opponent}</div>
                    <div className="text-sm text-gray-500">{player.gameTime}</div>
                  </td>
                  <td className="px-4 py-4">{renderStars(player.matchupRating)}</td>
                  <td className="px-4 py-4">
                    <div className="text-sm text-blue-600 hover:text-blue-800 cursor-pointer max-w-md">
                      {player.news}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
