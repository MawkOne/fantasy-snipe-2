"use client"

import { useState, useRef, useEffect } from "react"
import { Bot, Settings } from "lucide-react"

// TODO: Replace with real league members from Firebase
const members: Array<{
  id: number
  name: string
  avatar: string
  online: boolean
  team: string
  teamGoal: string
}> = []

interface ChatsSidebarProps {
  onOpenChat?: () => void
  onOpenAIChat?: () => void
  onOpenPressRequests?: () => void
  onOpenProfile?: () => void
  onOpenRoster?: () => void
  onOpenMemberChat?: () => void
  onOpenLeagues?: () => void
}

export function ChatsSidebar({
  onOpenChat,
  onOpenAIChat,
  onOpenPressRequests,
  onOpenProfile,
  onOpenRoster,
  onOpenMemberChat,
  onOpenLeagues,
}: ChatsSidebarProps) {
  const [width, setWidth] = useState(360)
  const [isResizing, setIsResizing] = useState(false)
  const [isMounted, setIsMounted] = useState(false)
  const sidebarRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return

      const leaguesSidebarWidth = 72 // Width of leagues sidebar on desktop
      const newWidth = e.clientX - leaguesSidebarWidth

      // Set min and max width constraints
      if (newWidth >= 280 && newWidth <= 500) {
        setWidth(newWidth)
      }
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    if (isResizing) {
      document.addEventListener("mousemove", handleMouseMove)
      document.addEventListener("mouseup", handleMouseUp)
      document.body.style.cursor = "col-resize"
      document.body.style.userSelect = "none"
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseup", handleMouseUp)
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
    }
  }, [isResizing])

  return (
    <div
      ref={sidebarRef}
      style={{ width: isMounted && window.innerWidth >= 768 ? `${width}px` : undefined }}
      className="flex-1 md:w-96 bg-white dark:bg-[#2f3136] border-r border-gray-200 dark:border-[#202225] flex flex-col relative min-w-0 transition-colors duration-300"
    >
      {/* Chat Items */}
      <div className="flex-1 overflow-y-auto pt-1">
        {/* General Chat */}
        <button onClick={onOpenChat} className="w-full py-2 px-3 hover:bg-gray-50 dark:hover:bg-[#40444b] flex items-center gap-2.5 transition-colors">
          <img src="/pool-logo.jpeg" alt="General Chat" className="w-10 h-10 rounded-full object-cover flex-shrink-0" />
          <div className="flex-1 text-left min-w-0">
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100 truncate">General Chat</h3>
              <span className="text-[10px] text-gray-500 dark:text-gray-400 flex-shrink-0">2:03 PM</span>
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400 truncate">You: I was really hoping Wolf was Can...</p>
          </div>
        </button>

        {/* AI Chat */}
        <button
          onClick={onOpenAIChat}
          className="w-full py-2 px-3 hover:bg-gray-50 dark:hover:bg-[#40444b] flex items-center gap-2.5 transition-colors"
        >
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1 text-left min-w-0">
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100 truncate">League AI </h3>
              <span className="text-[10px] text-gray-500 dark:text-gray-400 flex-shrink-0">10:39 AM</span>
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400 truncate">AI: Rules, events, stats and more...</p>
          </div>
        </button>

        {/* Press Requests - TEMPORARILY HIDDEN */}
        {/* <button
          onClick={onOpenPressRequests}
          className="w-full py-2 px-3 hover:bg-gray-50 dark:hover:bg-[#40444b] flex items-center gap-2.5 transition-colors"
        >
          <div className="relative flex-shrink-0">
            <img src="/man.jpg" alt="Press Requests" className="w-10 h-10 rounded-full object-cover" />
            <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-red-500 text-white text-[10px] font-semibold rounded-full flex items-center justify-center border-2 border-white dark:border-[#2f3136]">
              3
            </span>
          </div>
          <div className="flex-1 text-left min-w-0">
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100 truncate">AI Press </h3>
              <span className="text-[10px] text-gray-500 dark:text-gray-400 flex-shrink-0">Yesterday</span>
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400 truncate">No pending requests</p>
          </div>
        </button> */}

        {/* Members Section */}
        <div className="px-3 py-2 border-t border-gray-200 dark:border-[#202225] mt-1">
          <h2 className="text-[10px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">League Members</h2>
        </div>

        <button
          onClick={onOpenProfile}
          className="w-full py-2 px-3 bg-blue-50 dark:bg-[#292b2f] border-b border-blue-100 dark:border-[#202225] flex items-center gap-2.5 hover:bg-blue-100 dark:hover:bg-[#40444b] transition-colors"
        >
          <div className="relative flex-shrink-0">
            <img src="/man.jpg" alt="You" className="w-9 h-9 rounded-full object-cover" />
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-green-500 border-2 border-white dark:border-[#292b2f] rounded-full" />
          </div>
          <div className="flex-1 text-left min-w-0">
            <h3 className="font-medium text-sm text-gray-900 dark:text-gray-100 truncate">You</h3>
            <p className="text-[10px] text-gray-500 dark:text-gray-400 truncate">
              Wolves • Win Now • <span className="text-blue-600 dark:text-blue-400 hover:underline">Roster</span>
            </p>
          </div>
          <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0">
            <Settings className="w-4 h-4 text-gray-700 dark:text-gray-300" />
          </div>
        </button>

        {members.map((member) => (
          <button
            key={member.id}
            onClick={onOpenMemberChat}
            className="w-full py-2 px-3 hover:bg-gray-50 dark:hover:bg-[#40444b] flex items-center gap-2.5 transition-colors"
          >
            <div className="relative flex-shrink-0">
              <img
                src={member.avatar || "/placeholder.svg"}
                alt={member.name}
                className="w-9 h-9 rounded-full object-cover"
              />
              {member.online && (
                <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-green-500 border-2 border-white dark:border-[#2f3136] rounded-full" />
              )}
            </div>
            <div className="flex-1 text-left min-w-0">
              <h3 className="font-medium text-sm text-gray-900 dark:text-gray-100 truncate">{member.name}</h3>
              <p className="text-[10px] text-gray-500 dark:text-gray-400 truncate">
                {member.team} • {member.teamGoal} •{" "}
                <span
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                  onClick={(e) => {
                    e.stopPropagation()
                    onOpenRoster?.()
                  }}
                >
                  Roster
                </span>
              </p>
            </div>
          </button>
        ))}
      </div>

      <div
        className="hidden md:block absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-500 transition-colors z-10"
        onMouseDown={() => setIsResizing(true)}
      />
    </div>
  )
}
