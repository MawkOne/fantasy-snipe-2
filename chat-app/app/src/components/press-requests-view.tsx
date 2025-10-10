"use client"

import { useState } from "react"
import {
  ArrowLeft,
  Search,
  MoreHorizontal,
  ChevronDown,
  ChevronUp,
  Mic,
  EyeOff,
  MessageSquare,
  Plus,
  X,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

interface PressRequestsViewProps {
  onBack?: () => void
  onOpenVoiceInterview?: () => void
}

const pressItems = {
  podcast: [
    {
      id: "podcast-interview",
      type: "interview" as const,
      title: "Weekly Podcast Interview",
      description: "Share your thoughts on the league, recent moves, and strategy",
      context: "Weekly Podcast - Episode 12",
    },
    {
      id: 1,
      type: "trade" as const,
      teamA: "Wolves",
      teamB: "Dragons",
      teamAGives: ["Connor McDavid", "2025 1st Round Pick"],
      teamBGives: ["Auston Matthews", "Mitch Marner"],
      context: "Weekly Podcast - Episode 12",
    },
    {
      id: 2,
      type: "trade" as const,
      teamA: "Tigers",
      teamB: "Eagles",
      teamAGives: ["Nathan MacKinnon"],
      teamBGives: ["Leon Draisaitl", "2024 2nd Round Pick"],
      context: "Weekly Podcast - Episode 12",
    },
  ],
  midweek: [
    {
      id: 3,
      type: "rumor" as const,
      player: "Cale Makar",
      team: "Wolves",
      reason: "Team looking to rebuild after missing playoffs",
      source: "Anonymous GM",
      timestamp: "2 hours ago",
    },
    {
      id: 4,
      type: "rumor" as const,
      player: "Auston Matthews",
      team: "Dragons",
      reason: "GM exploring options to upgrade defense",
      source: "League Insider",
      timestamp: "5 hours ago",
    },
    {
      id: 5,
      type: "rumor" as const,
      player: "Nathan MacKinnon",
      team: "Tigers",
      reason: "Contract negotiations stalled, team may look to move",
      source: "Mike (Eagles)",
      timestamp: "1 day ago",
    },
  ],
}

const sourceOptions = [
  "Off the Record GM",
  "Player's Agent",
  "League Insider",
  "Anonymous Source",
  "A Little Birdie",
  "Unnamed Executive",
  "Sources Say",
  "Locker Room Whispers",
  "Front Office Leak",
  "My Cousin's Friend",
]

export function PressRequestsView({ onBack, onOpenVoiceInterview }: PressRequestsViewProps) {
  const [activeTab, setActiveTab] = useState<"podcast" | "midweek">("podcast")
  const [expandedCard, setExpandedCard] = useState<string | number | null>(null)
  const [isCreatingRumor, setIsCreatingRumor] = useState(false)
  const [newRumor, setNewRumor] = useState({
    source: "",
    reason: "",
    isAnonymous: true,
    leakPublic: false,
  })
  const [responses, setResponses] = useState<
    Record<string | number, { winner: string; comment: string; isAnonymous: boolean }>
  >({})
  const [noCommentItems, setNoCommentItems] = useState<Set<string | number>>(new Set())

  const currentItems = activeTab === "podcast" ? pressItems.podcast : pressItems.midweek

  const handleWinnerSelect = (itemId: string | number, winner: string) => {
    setResponses((prev) => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        winner,
        comment: prev[itemId]?.comment || "",
        isAnonymous: prev[itemId]?.isAnonymous ?? false,
      },
    }))
  }

  const handleCommentChange = (itemId: string | number, comment: string) => {
    setResponses((prev) => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        winner: prev[itemId]?.winner || "",
        comment,
        isAnonymous: prev[itemId]?.isAnonymous ?? false,
      },
    }))
  }

  const handleAnonymousToggle = (itemId: string | number) => {
    setResponses((prev) => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        winner: prev[itemId]?.winner || "",
        comment: prev[itemId]?.comment || "",
        isAnonymous: !prev[itemId]?.isAnonymous,
      },
    }))
  }

  const handleSubmit = (itemId: string | number) => {
    const response = responses[itemId]
    // Handle submission logic here
  }

  const handleTalkToAI = (itemId: string | number) => {
    // Handle opening AI chat interface
  }

  const handleOffRecord = (itemId: string | number) => {
    // Handle off-record comment
  }

  const toggleCard = (itemId: string | number) => {
    setExpandedCard(expandedCard === itemId ? null : itemId)
  }

  const handleVoiceInterview = () => {
    if (onOpenVoiceInterview) {
      onOpenVoiceInterview()
    }
  }

  const handleChatInterview = () => {
    // Handle chat interview
  }

  const handleStartRumor = () => {
    setIsCreatingRumor(true)
  }

  const handleCancelRumor = () => {
    setIsCreatingRumor(false)
    setNewRumor({ source: "", reason: "", isAnonymous: true, leakPublic: false })
  }

  const handleSubmitRumor = () => {
    // Handle submitting the new rumor
    setIsCreatingRumor(false)
    setNewRumor({ source: "", reason: "", isAnonymous: true, leakPublic: false })
  }

  const handleNoComment = (itemId: string | number) => {
    setNoCommentItems((prev) => new Set(prev).add(itemId))
  }

  const handleUndoNoComment = (itemId: string | number) => {
    setNoCommentItems((prev) => {
      const newSet = new Set(prev)
      newSet.delete(itemId)
      return newSet
    })
  }

  return (
    <div className="flex-1 flex flex-col bg-[#f0ebe3]">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <button
              onClick={onBack}
              className="md:hidden w-9 h-9 rounded-full hover:bg-gray-100 flex items-center justify-center transition-colors flex-shrink-0"
            >
              <ArrowLeft className="w-5 h-5 text-gray-700" />
            </button>

            <div className="relative flex-shrink-0">
              <img src="/man.jpg" alt="Press Requests" className="w-10 h-10 rounded-full object-cover" />
              {currentItems.filter((item) => !noCommentItems.has(item.id)).length > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-semibold rounded-full flex items-center justify-center border-2 border-white">
                  {currentItems.filter((item) => !noCommentItems.has(item.id)).length}
                </span>
              )}
            </div>

            <div className="flex-1 min-w-0">
              <h2 className="font-semibold text-gray-900 truncate">Press Requests</h2>
              <p className="text-xs text-gray-500 truncate">Trade Analysis & Commentary</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button className="w-9 h-9 rounded-full hover:bg-gray-100 flex items-center justify-center transition-colors">
              <Search className="w-5 h-5 text-gray-600" />
            </button>
            <button className="w-9 h-9 rounded-full hover:bg-gray-100 flex items-center justify-center transition-colors">
              <MoreHorizontal className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>

        <div className="flex gap-2 mt-3 border-b border-gray-200">
          <button
            onClick={() => setActiveTab("podcast")}
            className={`px-4 py-2 font-medium text-sm transition-colors relative ${
              activeTab === "podcast" ? "text-blue-600" : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Weekly Podcast
            {activeTab === "podcast" && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-full" />
            )}
          </button>
          <button
            onClick={() => setActiveTab("midweek")}
            className={`px-4 py-2 font-medium text-sm transition-colors relative ${
              activeTab === "midweek" ? "text-blue-600" : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Rumour Mill
            {activeTab === "midweek" && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-full" />
            )}
          </button>
        </div>
      </div>

      {/* Items List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {activeTab === "midweek" && !isCreatingRumor && (
          <Button onClick={handleStartRumor} className="w-full flex items-center justify-center gap-2 py-6">
            <Plus className="w-5 h-5" />
            <span className="font-medium">Start a Rumor</span>
          </Button>
        )}

        {activeTab === "midweek" && isCreatingRumor && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <h3 className="font-semibold text-gray-900 mb-4">Start a Rumor</h3>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Source</label>
                <select
                  value={newRumor.source}
                  onChange={(e) => setNewRumor({ ...newRumor, source: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="">Select a source...</option>
                  {sourceOptions.map((source) => (
                    <option key={source} value={source}>
                      {source}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">What's the rumor?</label>
                <Textarea
                  placeholder="e.g., Connor McDavid might be available as the Wolves look to rebuild..."
                  value={newRumor.reason}
                  onChange={(e) => setNewRumor({ ...newRumor, reason: e.target.value })}
                  className="w-full min-h-[100px]"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="leak-public"
                    checked={newRumor.leakPublic}
                    onChange={(e) => setNewRumor({ ...newRumor, leakPublic: e.target.checked })}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="leak-public" className="text-sm text-gray-700">
                    Leak it Public
                  </label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="anonymous-rumor"
                    checked={newRumor.isAnonymous}
                    onChange={(e) => setNewRumor({ ...newRumor, isAnonymous: e.target.checked })}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="anonymous-rumor" className="text-sm text-gray-700">
                    Post anonymously
                  </label>
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                <Button onClick={handleSubmitRumor} disabled={!newRumor.source || !newRumor.reason} className="flex-1">
                  Post Rumor
                </Button>
                <Button onClick={handleCancelRumor} variant="outline" className="flex-1 bg-transparent">
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}

        {currentItems.map((item) => {
          const isExpanded = expandedCard === item.id
          const response = responses[item.id]
          const isNoComment = noCommentItems.has(item.id)

          if (item.type === "interview") {
            return (
              <div
                key={item.id}
                className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 ${
                  isNoComment ? "opacity-50 cursor-pointer hover:opacity-60" : ""
                }`}
                onClick={isNoComment ? () => handleUndoNoComment(item.id) : undefined}
              >
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-lg">{item.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                  </div>

                  {/* Deadline */}
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                    <p className="text-sm font-medium text-amber-900">Deadline: Friday, March 15 at 5:00 PM EST</p>
                  </div>

                  {/* Topics & Questions */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Topics & Questions:</h4>
                    <ul className="space-y-2">
                      <li className="flex items-start gap-2">
                        <span className="text-blue-600 font-semibold mt-0.5">•</span>
                        <span className="text-sm text-gray-700">What's your strategy heading into the playoffs?</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-blue-600 font-semibold mt-0.5">•</span>
                        <span className="text-sm text-gray-700">
                          How do you feel about the recent trades in the league?
                        </span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-blue-600 font-semibold mt-0.5">•</span>
                        <span className="text-sm text-gray-700">
                          Who do you see as the biggest threat to your championship run?
                        </span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-blue-600 font-semibold mt-0.5">•</span>
                        <span className="text-sm text-gray-700">Any players you're targeting for next season?</span>
                      </li>
                    </ul>
                  </div>

                  {/* Interview Options */}
                  <div className="grid grid-cols-3 gap-2 pt-2">
                    <Button
                      onClick={handleVoiceInterview}
                      disabled={isNoComment}
                      className="flex flex-col items-center justify-center gap-1 h-auto py-3"
                    >
                      <Mic className="w-4 h-4" />
                      <div className="text-xs">Voice Interview</div>
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleChatInterview}
                      disabled={isNoComment}
                      className="flex flex-col items-center justify-center gap-1 h-auto py-3 bg-transparent"
                    >
                      <MessageSquare className="w-4 h-4" />
                      <div className="text-xs">Chat Interview</div>
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleNoComment(item.id)}
                      disabled={isNoComment}
                      className="flex flex-col items-center justify-center gap-1 h-auto py-3 bg-transparent border-gray-300 text-gray-600 hover:bg-gray-50"
                    >
                      <X className="w-4 h-4" />
                      <div className="text-xs">No Comment</div>
                    </Button>
                  </div>
                </div>
              </div>
            )
          }

          if (item.type === "rumor") {
            return (
              <div
                key={item.id}
                className={`bg-white rounded-lg shadow-sm border border-gray-200 ${isNoComment ? "opacity-50 cursor-pointer hover:opacity-60" : ""}`}
                onClick={isNoComment ? () => handleUndoNoComment(item.id) : undefined}
              >
                <button
                  onClick={() => toggleCard(item.id)}
                  className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <div className="text-left flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-orange-600 bg-orange-50 px-2 py-0.5 rounded">
                        RUMOR
                      </span>
                      <span className="text-xs text-gray-500">{item.timestamp}</span>
                    </div>
                    <p className="font-semibold text-gray-900">
                      {item.player} <span className="text-gray-500 font-normal">({item.team})</span>
                    </p>
                    <p className="text-sm text-gray-600 mt-1">{item.reason}</p>
                  </div>
                  {isExpanded ? (
                    <ChevronUp className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  )}
                </button>

                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-gray-100 pt-4">
                    <div className="space-y-3">
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Source</p>
                        <p className="text-sm font-medium text-gray-900">{item.source}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Details</p>
                        <p className="text-sm text-gray-700">{item.reason}</p>
                      </div>
                      <div className="pt-2">
                        <p className="text-sm font-medium text-gray-900 mb-2">How interesting is this?</p>
                        <div className="grid grid-cols-3 gap-2">
                          <Button
                            variant="outline"
                            disabled={isNoComment}
                            className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white border-0 hover:from-orange-600 hover:to-red-600"
                          >
                            Holy #$%#
                          </Button>
                          <Button
                            variant="outline"
                            disabled={isNoComment}
                            className="w-full bg-blue-500 text-white border-0 hover:bg-blue-600"
                          >
                            Interesting
                          </Button>
                          <Button
                            variant="outline"
                            disabled={isNoComment}
                            className="w-full bg-gray-400 text-white border-0 hover:bg-gray-500"
                          >
                            Big Whoop.
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          }

          return (
            <div
              key={item.id}
              className={`bg-white rounded-lg shadow-sm border border-gray-200 ${isNoComment ? "opacity-50 cursor-pointer hover:opacity-60" : ""}`}
              onClick={isNoComment ? () => handleUndoNoComment(item.id) : undefined}
            >
              <button
                onClick={() => toggleCard(item.id)}
                className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="text-left flex-1">
                  <p className="text-xs text-gray-500 mb-2">Trade</p>
                  <div className="space-y-1">
                    <p className="text-sm text-gray-900">
                      <span className="font-semibold">{item.teamA}:</span> {item.teamAGives.join(", ")}
                    </p>
                    <p className="text-sm text-gray-900">
                      <span className="font-semibold">{item.teamB}:</span> {item.teamBGives.join(", ")}
                    </p>
                  </div>
                </div>
                {isExpanded ? (
                  <ChevronUp className="w-5 h-5 text-gray-400 flex-shrink-0" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                )}
              </button>

              {isExpanded && (
                <div className="px-4 pb-4 border-t border-gray-100 pt-4">
                  <div className="space-y-2 mb-4">
                    <div className="flex items-start gap-2">
                      <span className="font-semibold text-gray-900 min-w-[80px]">{item.teamA}:</span>
                      <span className="text-gray-700">{item.teamAGives.join(", ")}</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="font-semibold text-gray-900 min-w-[80px]">{item.teamB}:</span>
                      <span className="text-gray-700">{item.teamBGives.join(", ")}</span>
                    </div>
                  </div>

                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-900 mb-2">Who won the trade?</p>
                    <div className="flex gap-2">
                      <Button
                        variant={response?.winner === item.teamA ? "default" : "outline"}
                        size="sm"
                        onClick={() => handleWinnerSelect(item.id, item.teamA)}
                        className="flex-1"
                      >
                        {item.teamA}
                      </Button>
                      <Button
                        variant={response?.winner === "Fair" ? "default" : "outline"}
                        size="sm"
                        onClick={() => handleWinnerSelect(item.id, "Fair")}
                        className="flex-1"
                      >
                        Fair Trade
                      </Button>
                      <Button
                        variant={response?.winner === item.teamB ? "default" : "outline"}
                        size="sm"
                        onClick={() => handleWinnerSelect(item.id, item.teamB)}
                        className="flex-1"
                      >
                        {item.teamB}
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-900 mb-2">Share your thoughts:</p>
                    <div className="grid grid-cols-3 gap-2">
                      <Button
                        variant="outline"
                        onClick={() => handleTalkToAI(item.id)}
                        disabled={isNoComment}
                        className="flex flex-col items-center justify-center gap-1 h-auto py-3"
                      >
                        <Mic className="w-4 h-4" />
                        <div className="text-xs">Talk to AI</div>
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => handleOffRecord(item.id)}
                        disabled={isNoComment}
                        className="flex flex-col items-center justify-center gap-1 h-auto py-3"
                      >
                        <EyeOff className="w-4 h-4" />
                        <div className="text-xs">Off Record</div>
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => handleNoComment(item.id)}
                        disabled={isNoComment}
                        className="flex flex-col items-center justify-center gap-1 h-auto py-3 bg-transparent border-gray-300 text-gray-600 hover:bg-gray-50"
                      >
                        <X className="w-4 h-4" />
                        <div className="text-xs">No Comment</div>
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
