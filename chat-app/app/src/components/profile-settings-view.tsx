"use client"

import { useState, useEffect } from "react"
import { ArrowLeft, Mail, Phone, User, X, Clock } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"

interface ProfileSettingsViewProps {
  onBack: () => void
}

// Mock player data for No Trade List
const allPlayers = [
  { id: 1, name: "Connor McDavid", team: "EDM", position: "C" },
  { id: 2, name: "Auston Matthews", team: "TOR", position: "C" },
  { id: 3, name: "Nathan MacKinnon", team: "COL", position: "C" },
  { id: 4, name: "Cale Makar", team: "COL", position: "D" },
  { id: 5, name: "Leon Draisaitl", team: "EDM", position: "C" },
  { id: 6, name: "David Pastrnak", team: "BOS", position: "RW" },
  { id: 7, name: "Nikita Kucherov", team: "TBL", position: "RW" },
  { id: 8, name: "Igor Shesterkin", team: "NYR", position: "G" },
]

const gmInterest: Record<number, Array<{ id: number; name: string; team: string }>> = {
  1: [
    { id: 1, name: "Mike Chen", team: "Dragons" },
    { id: 2, name: "Sarah Johnson", team: "Eagles" },
  ],
  2: [{ id: 3, name: "Tom Wilson", team: "Hawks" }],
  4: [
    { id: 1, name: "Mike Chen", team: "Dragons" },
    { id: 4, name: "Lisa Park", team: "Tigers" },
    { id: 5, name: "John Smith", team: "Bears" },
  ],
  5: [{ id: 2, name: "Sarah Johnson", team: "Eagles" }],
}

export function ProfileSettingsView({ onBack }: ProfileSettingsViewProps) {
  const [email, setEmail] = useState("rob.innes@email.com")
  const [phone, setPhone] = useState("+1 (555) 123-4567")
  const [teamGoal, setTeamGoal] = useState<"win-now" | "win-next-year" | "rebuild">("win-now")
  const [tradingStatus, setTradingStatus] = useState<"open" | "not-now">("open")
  const [customStatus, setCustomStatus] = useState("")
  const [noTradeList, setNoTradeList] = useState<number[]>([1, 4])

  const [countdown, setCountdown] = useState({ months: 0, days: 0, hours: 0, minutes: 0 })

  const tradeDeadline = new Date("2026-03-07T15:00:00")

  useEffect(() => {
    const calculateCountdown = () => {
      const now = new Date()
      const diff = tradeDeadline.getTime() - now.getTime()

      if (diff > 0) {
        const months = Math.floor(diff / (1000 * 60 * 60 * 24 * 30))
        const days = Math.floor((diff % (1000 * 60 * 60 * 24 * 30)) / (1000 * 60 * 60 * 24))
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))

        setCountdown({ months, days, hours, minutes })
      }
    }

    calculateCountdown()
    const interval = setInterval(calculateCountdown, 60000) // Update every minute

    return () => clearInterval(interval)
  }, [])

  const togglePlayer = (playerId: number) => {
    setNoTradeList((prev) => (prev.includes(playerId) ? prev.filter((id) => id !== playerId) : [...prev, playerId]))
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
          <div className="flex items-center gap-3 flex-1">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
              <User className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Profile Settings</h1>
              <p className="text-sm text-gray-500">Wolves</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Contact Information */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h2>
            <div className="space-y-4">
              <div>
                <Label htmlFor="email" className="text-sm font-medium text-gray-700 mb-1.5 flex items-center gap-2">
                  <Mail className="w-4 h-4" />
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full"
                />
              </div>
              <div>
                <Label htmlFor="phone" className="text-sm font-medium text-gray-700 mb-1.5 flex items-center gap-2">
                  <Phone className="w-4 h-4" />
                  Phone
                </Label>
                <Input
                  id="phone"
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full"
                />
              </div>
            </div>
          </div>

          {/* Team Goal */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Team Goal</h2>
            <p className="text-sm text-gray-600 mb-4">Select your strategy for this season</p>
            <div className="space-y-3">
              <label className="flex items-center gap-3 p-4 border-2 rounded-lg cursor-pointer transition-colors hover:bg-gray-50 has-[:checked]:border-green-500 has-[:checked]:bg-green-50">
                <input
                  type="radio"
                  name="team-goal"
                  value="win-now"
                  checked={teamGoal === "win-now"}
                  onChange={() => setTeamGoal("win-now")}
                  className="w-4 h-4 text-green-600"
                />
                <div>
                  <div className="font-semibold text-gray-900">Win Now</div>
                  <div className="text-sm text-gray-600">Competing for the championship this season</div>
                </div>
              </label>

              <label className="flex items-center gap-3 p-4 border-2 rounded-lg cursor-pointer transition-colors hover:bg-gray-50 has-[:checked]:border-blue-500 has-[:checked]:bg-blue-50">
                <input
                  type="radio"
                  name="team-goal"
                  value="win-next-year"
                  checked={teamGoal === "win-next-year"}
                  onChange={() => setTeamGoal("win-next-year")}
                  className="w-4 h-4 text-blue-600"
                />
                <div>
                  <div className="font-semibold text-gray-900">Win Next Year</div>
                  <div className="text-sm text-gray-600">Building for next season's championship run</div>
                </div>
              </label>

              <label className="flex items-center gap-3 p-4 border-2 rounded-lg cursor-pointer transition-colors hover:bg-gray-50 has-[:checked]:border-orange-500 has-[:checked]:bg-orange-50">
                <input
                  type="radio"
                  name="team-goal"
                  value="rebuild"
                  checked={teamGoal === "rebuild"}
                  onChange={() => setTeamGoal("rebuild")}
                  className="w-4 h-4 text-orange-600"
                />
                <div>
                  <div className="font-semibold text-gray-900">Rebuild</div>
                  <div className="text-sm text-gray-600">Focusing on long-term development and draft picks</div>
                </div>
              </label>
            </div>
          </div>

          {/* Trading Status */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Trading Status</h2>
            <p className="text-sm text-gray-600 mb-4">Let other GMs know if you're open to trade discussions</p>
            <div className="space-y-4">
              <div className="space-y-3">
                <label className="flex items-center gap-3 p-4 border-2 rounded-lg cursor-pointer transition-colors hover:bg-gray-50 has-[:checked]:border-green-500 has-[:checked]:bg-green-50">
                  <input
                    type="radio"
                    name="trading-status"
                    value="open"
                    checked={tradingStatus === "open"}
                    onChange={() => setTradingStatus("open")}
                    className="w-4 h-4 text-green-600"
                  />
                  <div>
                    <div className="font-semibold text-gray-900">Open for Trades</div>
                    <div className="text-sm text-gray-600">Actively looking at trade offers</div>
                  </div>
                </label>

                <label className="flex flex-col gap-3 p-4 border-2 rounded-lg cursor-pointer transition-colors hover:bg-gray-50 has-[:checked]:border-gray-500 has-[:checked]:bg-gray-50">
                  <div className="flex items-center gap-3">
                    <input
                      type="radio"
                      name="trading-status"
                      value="not-now"
                      checked={tradingStatus === "not-now"}
                      onChange={() => setTradingStatus("not-now")}
                      className="w-4 h-4 text-gray-600"
                    />
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900">Not Now</div>
                      <div className="text-sm text-gray-600">Not actively looking at trades at the moment</div>
                    </div>
                  </div>
                  {tradingStatus === "not-now" && (
                    <div className="ml-7" onClick={(e) => e.stopPropagation()}>
                      <Input
                        placeholder="Set custom status (e.g., 'Checking back after playoffs')"
                        value={customStatus}
                        onChange={(e) => setCustomStatus(e.target.value)}
                        className="w-full"
                      />
                    </div>
                  )}
                </label>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Clock className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900 mb-1">Trade Deadline</div>
                    <div className="text-sm text-gray-700 mb-2">March 7, 2026 at 3:00 PM EST</div>
                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex flex-col items-center">
                        <span className="text-2xl font-bold text-blue-600">{countdown.months}</span>
                        <span className="text-xs text-gray-600">months</span>
                      </div>
                      <div className="flex flex-col items-center">
                        <span className="text-2xl font-bold text-blue-600">{countdown.days}</span>
                        <span className="text-xs text-gray-600">days</span>
                      </div>
                      <div className="flex flex-col items-center">
                        <span className="text-2xl font-bold text-blue-600">{countdown.hours}</span>
                        <span className="text-xs text-gray-600">hours</span>
                      </div>
                      <div className="flex flex-col items-center">
                        <span className="text-2xl font-bold text-blue-600">{countdown.minutes}</span>
                        <span className="text-xs text-gray-600">mins</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* No Trade List */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Trade List</h2>
            <p className="text-sm text-gray-600 mb-4">
              Select players you don't want to trade ({noTradeList.length} selected)
            </p>
            <div className="space-y-2">
              {allPlayers.map((player) => {
                const isSelected = noTradeList.includes(player.id)
                const interestedGMs = gmInterest[player.id] || []
                return (
                  <button
                    key={player.id}
                    onClick={() => togglePlayer(player.id)}
                    className={`w-full flex items-center justify-between p-3 rounded-lg border-2 transition-colors ${
                      isSelected ? "border-red-500 bg-red-50" : "border-gray-200 hover:bg-gray-50 hover:border-gray-300"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                          isSelected ? "bg-red-500 border-red-500" : "border-gray-300"
                        }`}
                      >
                        {isSelected && <X className="w-3 h-3 text-white" strokeWidth={3} />}
                      </div>
                      <div className="text-left">
                        <div className="font-medium text-gray-900">{player.name}</div>
                        <div className="text-sm text-gray-600">
                          {player.team} • {player.position}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {interestedGMs.length > 0 && (
                        <div className="flex items-center -space-x-2">
                          {interestedGMs.slice(0, 3).map((gm) => (
                            <div
                              key={gm.id}
                              className="w-8 h-8 rounded-full bg-blue-500 border-2 border-white flex items-center justify-center"
                              title={`${gm.name} (${gm.team}) is interested`}
                            >
                              <span className="text-xs font-semibold text-white">{gm.name.charAt(0)}</span>
                            </div>
                          ))}
                          {interestedGMs.length > 3 && (
                            <div
                              className="w-8 h-8 rounded-full bg-gray-500 border-2 border-white flex items-center justify-center"
                              title={`${interestedGMs.length - 3} more GMs interested`}
                            >
                              <span className="text-xs font-semibold text-white">+{interestedGMs.length - 3}</span>
                            </div>
                          )}
                        </div>
                      )}
                      {isSelected && <span className="text-xs font-semibold text-red-600 uppercase">Protected</span>}
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end gap-3 pb-4">
            <Button variant="outline" onClick={onBack}>
              Cancel
            </Button>
            <Button className="bg-blue-600 hover:bg-blue-700">Save Changes</Button>
          </div>
        </div>
      </div>
    </div>
  )
}
