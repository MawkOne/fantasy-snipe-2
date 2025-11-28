import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import Image from "next/image"

export default function MockDraftSection() {
  const players = [
    {
      name: "Connor McDavid",
      team: "EDM",
      position: "C",
      overall: 1,
      percentage: "89%",
      image: "/hockey-player-headshot.png",
    },
    {
      name: "Leon Draisaitl",
      team: "EDM",
      position: "C/RW",
      overall: 2,
      percentage: "76%",
      image: "/hockey-player-headshot.png",
    },
    {
      name: "Nathan MacKinnon",
      team: "COL",
      position: "C",
      overall: 3,
      percentage: "68%",
      image: "/hockey-player-headshot.png",
    },
  ]

  return (
    <div className="mb-8">
      <div className="bg-gradient-to-r from-orange-400 to-orange-600 rounded-lg p-8 text-white mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">PRACTICE MAKES</h1>
            <h1 className="text-4xl font-bold mb-4">PLAYOFFS</h1>
            <Button className="bg-yellow-400 text-black hover:bg-yellow-300 font-semibold">Start a Mock</Button>
          </div>
          <div className="space-y-4">
            {players.map((player, index) => (
              <Card key={index} className="p-4 bg-white text-black flex items-center space-x-4 min-w-[300px]">
                <Image
                  src={player.image || "/placeholder.svg"}
                  alt={player.name}
                  width={50}
                  height={50}
                  className="rounded-full"
                />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold">{player.name}</h3>
                    <span className="text-green-600 font-bold">{player.percentage}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>
                      {player.team} {player.position}
                    </span>
                    <span>Overall {player.overall}</span>
                  </div>
                </div>
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                  Draft
                </Button>
              </Card>
            ))}
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold mb-4">Fast, Free Mock Drafts</h2>
        <p className="text-gray-600 mb-2">
          by <span className="text-blue-600">FantasySnipe.ai Staff</span> | August 2, 2025
        </p>
        <p className="text-gray-700">
          Practice for your draft with fast mocks against realistic opponents. Test strategies, draft from any position,
          and get grades instantly. <span className="text-blue-600 cursor-pointer">read more</span>
        </p>
      </div>
    </div>
  )
}
