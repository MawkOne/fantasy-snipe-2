"use client"

import { ChevronLeft, Play } from "lucide-react"

interface Episode {
  id: number
  title: string
  date: string
  duration: string
  description: string
  listened: boolean
}

const episodes: Episode[] = [
  {
    id: 1,
    title: "Week 12 Recap: Playoff Push Begins",
    date: "March 10, 2025",
    duration: "45:23",
    description: "Breaking down the biggest trades and playoff implications",
    listened: false,
  },
  {
    id: 2,
    title: "Trade Deadline Special",
    date: "March 3, 2025",
    duration: "52:18",
    description: "Live reactions to all the deadline day moves",
    listened: true,
  },
  {
    id: 3,
    title: "Mid-Season Awards & Predictions",
    date: "February 24, 2025",
    duration: "38:45",
    description: "Who's winning MVP? Championship favorites revealed",
    listened: true,
  },
  {
    id: 4,
    title: "Week 8 Roundtable Discussion",
    date: "February 17, 2025",
    duration: "41:30",
    description: "Special guests join to discuss league standings",
    listened: true,
  },
  {
    id: 5,
    title: "Draft Strategy Deep Dive",
    date: "February 10, 2025",
    duration: "49:12",
    description: "Looking ahead to next season's draft picks",
    listened: true,
  },
]

interface PodcastEpisodesSidebarProps {
  onBack: () => void
  onSelectEpisode: (episodeId: number) => void
}

export function PodcastEpisodesSidebar({ onBack, onSelectEpisode }: PodcastEpisodesSidebarProps) {
  return (
    <div className="w-full md:w-96 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="flex items-center gap-3 mb-4">
          <button onClick={onBack} className="md:hidden p-2 hover:bg-gray-100 rounded-full transition-colors">
            <ChevronLeft className="w-5 h-5 text-gray-700" />
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Podcast Episodes</h1>
        </div>
        <p className="text-sm text-gray-600">Listen to past episodes and league discussions</p>
      </div>

      {/* Episodes List */}
      <div className="flex-1 overflow-y-auto">
        {episodes.map((episode) => (
          <button
            key={episode.id}
            onClick={() => onSelectEpisode(episode.id)}
            className="w-full p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors text-left"
          >
            <div className="flex items-start gap-3">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
                <Play className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-gray-900 truncate flex-1">{episode.title}</h3>
                  <span
                    className={`text-xs font-medium px-2 py-1 rounded-full whitespace-nowrap ${
                      episode.listened ? "bg-gray-100 text-gray-600" : "bg-blue-100 text-blue-700"
                    }`}
                  >
                    {episode.listened ? "Listened" : "New Episode"}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2 line-clamp-2">{episode.description}</p>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span>{episode.date}</span>
                  <span>•</span>
                  <span>{episode.duration}</span>
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
