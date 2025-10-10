"use client"

import { useState, useRef, useEffect } from "react"
import { Bot, Settings } from "lucide-react"

const members = [
  { id: 1, name: "Rob Innes", avatar: "/man.jpg", online: true, team: "Wolves", teamGoal: "Win Now" },
  {
    id: 2,
    name: "Don Henderson",
    avatar: "/diverse-group-athletes.png",
    online: true,
    team: "Thunder",
    teamGoal: "Rebuild",
  },
  {
    id: 3,
    name: "Dave Wilson",
    avatar: "/diverse-group.png",
    online: false,
    team: "Eagles",
    teamGoal: "Win Next Year",
  },
  {
    id: 4,
    name: "Sarah Chen",
    avatar: "/diverse-woman-portrait.png",
    online: true,
    team: "Lions",
    teamGoal: "Win Now",
  },
  { id: 5, name: "Mike Torres", avatar: "/man-2.jpg", online: false, team: "Hawks", teamGoal: "Rebuild" },
]

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
  const sidebarRef = useRef<HTMLDivElement>(null)

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
      style={{ width: typeof window !== "undefined" && window.innerWidth >= 768 ? `${width}px` : undefined }}
      className="flex-1 md:w-96 bg-white border-r border-gray-200 flex flex-col relative min-w-0"
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-3 min-w-0">
          <img src="/pool-logo.jpeg" alt="UHHP Logo" className="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
          <h1 className="text-2xl font-bold text-gray-900 truncate">UHHP</h1>
        </div>
      </div>

      {/* Chat Items */}
      <div className="flex-1 overflow-y-auto">
        {/* General Chat */}
        <button onClick={onOpenChat} className="w-full p-3 hover:bg-gray-50 flex items-center gap-3 transition-colors">
          <img src="/pool-logo.jpeg" alt="General Chat" className="w-14 h-14 rounded-full object-cover flex-shrink-0" />
          <div className="flex-1 text-left min-w-0">
            <div className="flex items-center justify-between mb-1 gap-2">
              <h3 className="font-semibold text-gray-900 truncate">General Chat</h3>
              <span className="text-xs text-gray-500 flex-shrink-0">2:03 PM</span>
            </div>
            <p className="text-sm text-gray-600 truncate">You: I was really hoping Wolf was Can...</p>
          </div>
        </button>

        {/* AI Chat */}
        <button
          onClick={onOpenAIChat}
          className="w-full p-3 hover:bg-gray-50 flex items-center gap-3 transition-colors"
        >
          <div className="w-14 h-14 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0">
            <Bot className="w-7 h-7 text-white" />
          </div>
          <div className="flex-1 text-left min-w-0">
            <div className="flex items-center justify-between mb-1 gap-2">
              <h3 className="font-semibold text-gray-900 truncate">League AI </h3>
              <span className="text-xs text-gray-500 flex-shrink-0">10:39 AM</span>
            </div>
            <p className="text-sm text-gray-600 truncate">AI: Rules, events, stats and more...</p>
          </div>
        </button>

        {/* Press Requests */}
        <button
          onClick={onOpenPressRequests}
          className="w-full p-3 hover:bg-gray-50 flex items-center gap-3 transition-colors"
        >
          <div className="relative flex-shrink-0">
            <img src="/man.jpg" alt="Press Requests" className="w-14 h-14 rounded-full object-cover" />
            <span className="absolute -top-1 -right-1 w-6 h-6 bg-red-500 text-white text-xs font-semibold rounded-full flex items-center justify-center border-2 border-white">
              3
            </span>
          </div>
          <div className="flex-1 text-left min-w-0">
            <div className="flex items-center justify-between mb-1 gap-2">
              <h3 className="font-semibold text-gray-900 truncate">AI Press </h3>
              <span className="text-xs text-gray-500 flex-shrink-0">Yesterday</span>
            </div>
            <p className="text-sm text-gray-600 truncate">No pending requests</p>
          </div>
        </button>

        {/* Members Section */}
        <div className="px-4 py-3 border-t border-gray-200">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">League Members</h2>
        </div>

        <button
          onClick={onOpenProfile}
          className="w-full p-3 bg-blue-50 border-b border-blue-100 flex items-center gap-3 hover:bg-blue-100 transition-colors"
        >
          <div className="relative flex-shrink-0">
            <img src="/man.jpg" alt="You" className="w-12 h-12 rounded-full object-cover" />
            <span className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-green-500 border-2 border-white rounded-full" />
          </div>
          <div className="flex-1 text-left min-w-0">
            <h3 className="font-medium text-gray-900 truncate">You</h3>
            <p className="text-xs text-gray-500 truncate">
              Wolves • Win Now • <span className="text-blue-600 hover:underline">Roster</span>
            </p>
          </div>
          <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0">
            <Settings className="w-5 h-5 text-gray-700" />
          </div>
        </button>

        {members.map((member) => (
          <button
            key={member.id}
            onClick={onOpenMemberChat}
            className="w-full p-3 hover:bg-gray-50 flex items-center gap-3 transition-colors"
          >
            <div className="relative flex-shrink-0">
              <img
                src={member.avatar || "/placeholder.svg"}
                alt={member.name}
                className="w-12 h-12 rounded-full object-cover"
              />
              {member.online && (
                <span className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-green-500 border-2 border-white rounded-full" />
              )}
            </div>
            <div className="flex-1 text-left min-w-0">
              <h3 className="font-medium text-gray-900 truncate">{member.name}</h3>
              <p className="text-xs text-gray-500 truncate">
                {member.team} • {member.teamGoal} •{" "}
                <span
                  className="text-blue-600 hover:underline"
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
