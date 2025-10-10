"use client"

import { ChevronLeft, Play, Pause, SkipBack, SkipForward, Volume2 } from "lucide-react"
import { useState } from "react"

interface PodcastPlayerViewProps {
  onBack: () => void
  episodeId: number
}

const episodes = [
  {
    id: 1,
    title: "Week 12 Recap: Playoff Push Begins",
    date: "March 10, 2025",
    duration: "45:23",
    description: "Breaking down the biggest trades and playoff implications for the upcoming playoffs.",
    hosts: ["Mike Henderson", "Sarah Chen"],
    topics: [
      "Wolves vs Dragons trade analysis",
      "Playoff bracket predictions",
      "Injury report updates",
      "Waiver wire recommendations",
    ],
  },
  {
    id: 2,
    title: "Trade Deadline Special",
    date: "March 3, 2025",
    duration: "52:18",
    description: "Live reactions to all the deadline day moves and what they mean for your fantasy team.",
    hosts: ["Mike Henderson", "Sarah Chen", "Alex Rodriguez"],
    topics: ["Live trade reactions", "Winners and losers", "Playoff implications", "Emergency waiver adds"],
  },
  {
    id: 3,
    title: "Mid-Season Awards & Predictions",
    date: "February 24, 2025",
    duration: "38:45",
    description: "Who's winning MVP? Championship favorites revealed in our mid-season special.",
    hosts: ["Mike Henderson", "Sarah Chen"],
    topics: ["MVP candidates", "Championship predictions", "Breakout players", "Biggest disappointments"],
  },
]

export function PodcastPlayerView({ onBack, episodeId }: PodcastPlayerViewProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const episode = episodes.find((ep) => ep.id === episodeId) || episodes[0]

  // Mock total duration in seconds (45:23 = 2723 seconds)
  const totalDuration = 2723
  const progress = (currentTime / totalDuration) * 100

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  return (
    <div className="flex-1 flex flex-col bg-gradient-to-br from-purple-50 via-white to-indigo-50 h-full">
      {/* Header */}
      <div className="p-4 md:p-6 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors flex items-center justify-center"
          >
            <ChevronLeft className="w-5 h-5 text-gray-700" />
          </button>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900">Now Playing</h2>
            <p className="text-sm text-gray-600">UHHP Podcast</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8">
        <div className="max-w-3xl mx-auto space-y-8">
          {/* Episode Artwork */}
          <div className="w-full aspect-square max-w-md mx-auto rounded-2xl bg-gradient-to-br from-purple-500 via-indigo-600 to-blue-600 shadow-2xl flex items-center justify-center">
            <Play className="w-24 h-24 text-white opacity-90" />
          </div>

          {/* Episode Info */}
          <div className="text-center space-y-2">
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900">{episode.title}</h1>
            <p className="text-gray-600">{episode.date}</p>
            <p className="text-sm text-gray-500 max-w-2xl mx-auto">{episode.description}</p>
          </div>

          {/* Hosts */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Hosted by</h3>
            <div className="flex flex-wrap gap-2">
              {episode.hosts.map((host, index) => (
                <span key={index} className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
                  {host}
                </span>
              ))}
            </div>
          </div>

          {/* Topics Covered */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Topics Covered</h3>
            <ul className="space-y-2">
              {episode.topics.map((topic, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                  <span className="text-purple-500 mt-1">•</span>
                  <span>{topic}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Player Controls - Fixed at bottom */}
      <div className="bg-white border-t border-gray-200 p-4 md:p-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden cursor-pointer">
              <div
                className="h-full bg-gradient-to-r from-purple-500 to-indigo-600 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-500">
              <span>{formatTime(currentTime)}</span>
              <span>{episode.duration}</span>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-center gap-6">
            <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
              <SkipBack className="w-6 h-6 text-gray-700" />
            </button>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="w-14 h-14 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center hover:shadow-lg transition-all"
            >
              {isPlaying ? <Pause className="w-7 h-7 text-white" /> : <Play className="w-7 h-7 text-white ml-1" />}
            </button>
            <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
              <SkipForward className="w-6 h-6 text-gray-700" />
            </button>
          </div>

          {/* Volume */}
          <div className="flex items-center gap-3 max-w-xs mx-auto">
            <Volume2 className="w-5 h-5 text-gray-600" />
            <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-purple-500 to-indigo-600 w-3/4" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
