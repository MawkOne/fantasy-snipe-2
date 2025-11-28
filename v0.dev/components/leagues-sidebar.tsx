"use client"

import { MessagesSquare, RadioTower, Settings, Plus } from "lucide-react"
import { ThemeToggle } from "./theme-toggle"
import type { ChatType } from "./messenger-layout"
import { useLeagues } from "@/hooks/use-leagues"

interface LeaguesSidebarProps {
  onNavigate?: () => void
  onOpenChat?: () => void
  onOpenPodcast?: () => void
  activeChatType?: ChatType
  onCreateLeague?: () => void
}

export function LeaguesSidebar({ onNavigate, onOpenChat, onOpenPodcast, activeChatType, onCreateLeague }: LeaguesSidebarProps) {
  const isChatActive = activeChatType !== "podcast"
  const isPodcastActive = activeChatType === "podcast"
  
  // For demo purposes - replace with actual user ID from auth
  const DEMO_USER_ID = "user123"
  const { leagues, activeLeagueId, switchLeague, loading } = useLeagues(DEMO_USER_ID)

  return (
    <div className="lg:w-16 bg-white dark:bg-[#202225] border-r border-gray-200 dark:border-[#40444b] flex flex-col items-center py-3 gap-2.5 w-16 transition-colors duration-300">
      <div className="lg:hidden w-full mb-1 flex flex-col items-center">
        <h2 className="font-bold text-gray-900 dark:text-gray-100 text-center text-[10px] leading-tight mb-1">
          Snipe
          <br />
          Chat
        </h2>
        <button onClick={onNavigate} className="p-1 hover:bg-gray-100 dark:hover:bg-[#40444b] rounded-full"></button>
      </div>

      {/* Top Navigation Icons */}
      <button
        onClick={onOpenChat}
        className={`relative w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
          isChatActive ? "bg-blue-500 hover:bg-blue-600" : "bg-gray-100 dark:bg-[#40444b] hover:bg-gray-200 dark:hover:bg-[#2f3136]"
        }`}
      >
        <MessagesSquare className={`w-5 h-5 ${isChatActive ? "text-white" : "text-gray-700 dark:text-gray-300"}`} />
      </button>

      <button
        onClick={onOpenPodcast}
        className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
          isPodcastActive ? "bg-blue-500 hover:bg-blue-600" : "bg-gray-100 dark:bg-[#40444b] hover:bg-gray-200 dark:hover:bg-[#2f3136]"
        }`}
      >
        <RadioTower className={`w-5 h-5 ${isPodcastActive ? "text-white" : "text-gray-700 dark:text-gray-300"}`} />
      </button>

      <div className="h-px w-8 bg-gray-200 dark:bg-[#40444b] my-1" />

      {/* Loading State */}
      {loading && (
        <div className="w-10 h-10 rounded-full bg-gray-100 dark:bg-[#40444b] animate-pulse" />
      )}

      {/* Leagues */}
      {!loading && leagues.map((league) => (
        <button
          key={league.id}
          onClick={() => {
            switchLeague(league.id)
            onNavigate?.()
          }}
          className={`w-10 h-10 rounded-full overflow-hidden hover:opacity-90 transition-all border-2 ${
            activeLeagueId === league.id 
              ? "border-blue-500 ring-2 ring-blue-300 dark:ring-blue-700" 
              : "border-gray-200 dark:border-[#40444b]"
          }`}
          title={league.name}
        >
          <img 
            src={league.icon || "/pool-logo.jpeg"} 
            alt={league.name} 
            className="w-full h-full object-cover" 
          />
        </button>
      ))}

      {/* Add League Button */}
      <button
        onClick={onCreateLeague}
        className="w-10 h-10 rounded-full bg-gray-100 dark:bg-[#40444b] flex items-center justify-center hover:bg-gray-200 dark:hover:bg-[#2f3136] transition-colors border-2 border-dashed border-gray-300 dark:border-gray-600"
        title="Create New League"
      >
        <Plus className="w-5 h-5 text-gray-600 dark:text-gray-400" />
      </button>

      {/* Bottom Settings */}
      <div className="mt-auto flex flex-col items-center gap-2">
        <ThemeToggle />
        <button 
          className="w-10 h-10 rounded-full bg-gray-100 dark:bg-[#40444b] flex items-center justify-center hover:bg-gray-200 dark:hover:bg-[#2f3136] transition-colors"
          title="Settings"
        >
          <Settings className="w-5 h-5 text-gray-700 dark:text-gray-300" />
        </button>
      </div>
    </div>
  )
}
