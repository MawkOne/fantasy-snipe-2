"use client"

import { useState } from "react"
import { ArrowLeft, Star } from "lucide-react"
import { Button } from "@/components/ui/button"

interface RosterViewProps {
  onBack: () => void
  memberName?: string
  memberTeam?: string
  isOpenForTrades?: boolean
  tradingStatus?: "open" | "not-now"
  customStatus?: string
  teamGoal?: string // Added teamGoal prop
}

export function RosterView({
  onBack,
  memberName = "Rob Innes",
  memberTeam = "Wolves",
  isOpenForTrades = true,
  tradingStatus = "open",
  customStatus = "",
  teamGoal = "Win Now", // Added default team goal
}: RosterViewProps) {
  // Mock roster data with No Trade List status
  const roster = [
    { id: 1, name: "Connor McDavid", position: "C", team: "EDM", onNoTradeList: true },
    { id: 2, name: "Auston Matthews", position: "C", team: "TOR", onNoTradeList: true },
    { id: 3, name: "Nathan MacKinnon", position: "C", team: "COL", onNoTradeList: false },
    { id: 4, name: "Cale Makar", position: "D", team: "COL", onNoTradeList: true },
    { id: 5, name: "Leon Draisaitl", position: "C", team: "EDM", onNoTradeList: false },
    { id: 6, name: "David Pastrnak", position: "RW", team: "BOS", onNoTradeList: false },
    { id: 7, name: "Mikko Rantanen", position: "RW", team: "COL", onNoTradeList: false },
    { id: 8, name: "Quinn Hughes", position: "D", team: "VAN", onNoTradeList: true },
    { id: 9, name: "Igor Shesterkin", position: "G", team: "NYR", onNoTradeList: true },
    { id: 10, name: "Artemi Panarin", position: "LW", team: "NYR", onNoTradeList: false },
  ]

  const [interestedPlayers, setInterestedPlayers] = useState<number[]>([])
  const [myPlayersForTrade, setMyPlayersForTrade] = useState<number[]>([])

  // Mock roster for current user
  const myRoster = [
    { id: 101, name: "Sidney Crosby", position: "C", team: "PIT" },
    { id: 102, name: "Alex Ovechkin", position: "LW", team: "WSH" },
    { id: 103, name: "Erik Karlsson", position: "D", team: "PIT" },
    { id: 104, name: "Jack Hughes", position: "C", team: "NJD" },
    { id: 105, name: "Matthew Tkachuk", position: "LW", team: "FLA" },
    { id: 106, name: "Elias Pettersson", position: "C", team: "VAN" },
    { id: 107, name: "Roman Josi", position: "D", team: "NSH" },
    { id: 108, name: "Andrei Vasilevskiy", position: "G", team: "TBL" },
  ]

  const handleExpressInterest = (playerId: number) => {
    if (interestedPlayers.includes(playerId)) {
      setInterestedPlayers(interestedPlayers.filter((id) => id !== playerId))
    } else {
      setInterestedPlayers([...interestedPlayers, playerId])
    }
  }

  const handleToggleMyPlayer = (playerId: number) => {
    if (myPlayersForTrade.includes(playerId)) {
      setMyPlayersForTrade(myPlayersForTrade.filter((id) => id !== playerId))
    } else {
      setMyPlayersForTrade([...myPlayersForTrade, playerId])
    }
  }

  const handleRequestTradeTalk = () => {
    console.log("[v0] Requesting trade talk with", memberName)
    // This would open a chat or send a notification
  }

  return (
    <div className="flex-1 flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="md:hidden w-9 h-9 rounded-full hover:bg-gray-100 flex items-center justify-center transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-700" />
          </button>

          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-semibold text-gray-900 truncate">{memberName}'s Roster</h1>
            <p className="text-sm text-gray-500">{memberTeam}</p>
          </div>

          {isOpenForTrades && (
            <Button onClick={handleRequestTradeTalk}>
              <span className="hidden sm:inline">Request Trade Talk</span>
              <span className="sm:hidden">Trade Talk</span>
            </Button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto">
          <div
            className={`rounded-lg p-4 mb-6 ${
              tradingStatus === "open" ? "bg-green-50 border border-green-200" : "bg-gray-50 border border-gray-200"
            }`}
          >
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-semibold text-gray-900">Team Goal:</span>
              <span className="text-sm font-medium text-gray-700">{teamGoal}</span>
              <span className="text-gray-400">•</span>
              <span
                className={`text-sm font-semibold ${tradingStatus === "open" ? "text-green-900" : "text-gray-900"}`}
              >
                Trading Status:
              </span>
              <span className={`text-sm font-medium ${tradingStatus === "open" ? "text-green-700" : "text-gray-700"}`}>
                {tradingStatus === "open" ? "Open for Trades" : "Not Now"}
              </span>
              {customStatus && tradingStatus === "not-now" && (
                <>
                  <span className="text-gray-400">•</span>
                  <span className="text-sm text-gray-600">{customStatus}</span>
                </>
              )}
            </div>
          </div>

          {/* Roster Grid */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Player
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Position
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Team
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {roster.map((player) => (
                    <tr key={player.id} className={player.onNoTradeList ? "bg-gray-50" : "hover:bg-gray-50"}>
                      <td className="px-4 py-3">
                        <span className="font-medium text-gray-900">{player.name}</span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">{player.position}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{player.team}</td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {player.onNoTradeList ? (
                            <span className="text-sm font-medium text-gray-500">Won't Trade</span>
                          ) : (
                            <button
                              onClick={() => handleExpressInterest(player.id)}
                              className="w-8 h-8 rounded-full hover:bg-gray-100 flex items-center justify-center transition-colors flex-shrink-0"
                              title={interestedPlayers.includes(player.id) ? "Remove interest" : "Express interest"}
                            >
                              <Star
                                className={`w-5 h-5 ${
                                  interestedPlayers.includes(player.id)
                                    ? "fill-yellow-400 text-yellow-400"
                                    : "text-gray-400"
                                }`}
                              />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Trade Offer Section */}
          {interestedPlayers.length > 0 && (
            <div className="mt-6 bg-white rounded-lg border border-gray-200 p-4 space-y-4">
              <h3 className="font-semibold text-gray-900">Who would you think about moving</h3>
              <p className="text-sm text-gray-600">
                You've expressed interest in {interestedPlayers.length} player
                {interestedPlayers.length !== 1 ? "s" : ""}. Select players from your roster you'd be willing to include
                in a trade.
              </p>

              {/* Players they're interested in */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Players You Want:</h4>
                <div className="flex flex-wrap gap-2">
                  {interestedPlayers.map((playerId) => {
                    const player = roster.find((p) => p.id === playerId)
                    return (
                      player && (
                        <span
                          key={playerId}
                          className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                        >
                          {player.name}
                        </span>
                      )
                    )
                  })}
                </div>
              </div>

              {/* User's roster for trade */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Your Players you&#39;d consider (click to select):
                </h4>
                <div className="flex flex-wrap gap-2">
                  {myRoster.map((player) => (
                    <button
                      key={player.id}
                      onClick={() => handleToggleMyPlayer(player.id)}
                      className={`inline-flex items-center px-3 py-1 rounded-full text-sm transition-colors ${
                        myPlayersForTrade.includes(player.id)
                          ? "bg-green-500 text-white hover:bg-green-600"
                          : "bg-gray-100 text-gray-800 hover:bg-gray-200"
                      }`}
                    >
                      {player.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
