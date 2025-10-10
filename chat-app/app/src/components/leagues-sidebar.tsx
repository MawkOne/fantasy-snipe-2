"use client"

import { MessagesSquare, RadioTower, Settings, Plus } from "lucide-react"
import type { ChatType } from "./messenger-layout"

const leagues = [{ id: 1, name: "Henderson's League", icon: "/pool-logo.jpeg" }]

interface LeaguesSidebarProps {
  onNavigate?: () => void
  onOpenChat?: () => void
  onOpenPodcast?: () => void
  activeChatType?: ChatType
}

export function LeaguesSidebar({ onNavigate, onOpenChat, onOpenPodcast, activeChatType }: LeaguesSidebarProps) {
  const isChatActive = activeChatType !== "podcast"
  const isPodcastActive = activeChatType === "podcast"

  return (
    <div className="lg:w-20 bg-white border-r border-gray-200 flex flex-col items-center py-4 gap-4 w-20">
      <div className="lg:hidden w-full mb-2 flex flex-col items-center">
        <h2 className="font-bold text-gray-900 text-center text-xs leading-tight mb-1">
          Snipe
          <br />
          Chat
        </h2>
        <button onClick={onNavigate} className="p-1 hover:bg-gray-100 rounded-full"></button>
      </div>

      {/* Top Navigation Icons */}
      <button
        onClick={onOpenChat}
        className={`relative w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
          isChatActive ? "bg-blue-500 hover:bg-blue-600" : "bg-gray-100 hover:bg-gray-200"
        }`}
      >
        <MessagesSquare className={`w-6 h-6 ${isChatActive ? "text-white" : "text-gray-700"}`} />
        <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
          1
        </span>
      </button>

      <button
        onClick={onOpenPodcast}
        className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
          isPodcastActive ? "bg-blue-500 hover:bg-blue-600" : "bg-gray-100 hover:bg-gray-200"
        }`}
      >
        <RadioTower className={`w-6 h-6 ${isPodcastActive ? "text-white" : "text-gray-700"}`} />
      </button>

      <div className="h-px w-10 bg-gray-200 my-2" />

      {/* Leagues */}
      {leagues.map((league) => (
        <button
          key={league.id}
          onClick={onNavigate}
          className="w-12 h-12 rounded-full overflow-hidden hover:opacity-90 transition-opacity border-2 border-gray-200"
        >
          <img src={league.icon || "/placeholder.svg"} alt={league.name} className="w-full h-full object-cover" />
        </button>
      ))}

      <button
        onClick={() => console.log("Add league clicked")}
        className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 transition-colors border-2 border-dashed border-gray-300"
      >
        <Plus className="w-6 h-6 text-gray-600" />
      </button>

      {/* Bottom Settings */}
      <div className="mt-auto">
        <button className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 transition-colors">
          <Settings className="w-6 h-6 text-gray-700" />
        </button>
      </div>
    </div>
  )
}
