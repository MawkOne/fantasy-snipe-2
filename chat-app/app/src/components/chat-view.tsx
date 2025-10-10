"use client"

import {
  Search,
  MoreHorizontal,
  Plus,
  Smile,
  ArrowLeft,
  ImageIcon,
  BarChart3,
  Calendar,
  Laugh,
  Bot,
} from "lucide-react"
import { Input } from "@/components/ui/input"
import { useState } from "react"

interface ChatViewProps {
  onBack?: () => void
}

export function ChatView({ onBack }: ChatViewProps) {
  const [isContentMenuOpen, setIsContentMenuOpen] = useState(false)
  const [isAIMode, setIsAIMode] = useState(false)

  const messages = [
    {
      id: 1,
      sender: "Rob Innes",
      content: "How about those Flames",
      timestamp: "1:45 PM",
      isOwn: false,
      avatar: "/man.jpg",
    },
    {
      id: 2,
      sender: "Don Henderson",
      content: "Hard working and good goalie",
      timestamp: "1:46 PM",
      isOwn: false,
      avatar: "/placeholder.svg?key=don",
    },
    {
      id: 3,
      sender: "Rob Innes",
      content: "Yes Wolf is very good",
      timestamp: "2:01 PM",
      isOwn: false,
      avatar: "/man.jpg",
    },
    {
      id: 4,
      sender: "You",
      content: "Ya we were talking about it last night. And Skinner is so gone",
      timestamp: "2:02 PM",
      isOwn: true,
    },
    {
      id: 5,
      sender: "You",
      content: "I was really hoping Wolf was Canadian for the Olympics",
      timestamp: "2:03 PM",
      isOwn: true,
    },
  ]

  return (
    <div className="flex-1 flex flex-col bg-[#f0ebe3]">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-shrink-0">
          {onBack && (
            <button
              onClick={onBack}
              className="md:hidden w-9 h-9 rounded-full hover:bg-gray-100 flex items-center justify-center transition-colors -ml-2"
            >
              <ArrowLeft className="w-5 h-5 text-gray-700" />
            </button>
          )}
          <img src="/pool-logo.jpeg" alt="Henderson's" className="w-10 h-10 rounded-full object-cover" />
          <div>
            <h2 className="font-semibold text-gray-900">Henderson's</h2>
            <p className="text-xs text-gray-500">Don, Rob, You</p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <button className="hidden sm:flex w-9 h-9 rounded-full hover:bg-gray-100 items-center justify-center transition-colors">
            <Search className="w-5 h-5 text-gray-700" />
          </button>
          <button className="w-9 h-9 rounded-full hover:bg-gray-100 flex items-center justify-center transition-colors">
            <MoreHorizontal className="w-5 h-5 text-gray-700" />
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 min-h-0 overflow-y-auto px-6 py-4 bg-sidebar-border">
        {/* Date Separator */}
        <div className="flex justify-center mb-6">
          <div className="bg-white px-4 py-1.5 rounded-full shadow-sm">
            <span className="text-xs font-medium text-gray-700">Today</span>
          </div>
        </div>

        {/* Encryption Notice */}

        {/* Group Creation Notice */}

        {/* Messages */}
        <div className="space-y-2">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.isOwn ? "justify-end" : "justify-start"} gap-2`}>
              {!message.isOwn && (
                <img
                  src={message.avatar || "/placeholder.svg"}
                  alt={message.sender}
                  className="w-8 h-8 rounded-full object-cover flex-shrink-0 mt-1"
                />
              )}
              <div className={`max-w-[65%] ${message.isOwn ? "items-end" : "items-start"} flex flex-col`}>
                {!message.isOwn && (
                  <span className="text-xs font-medium text-teal-600 mb-0.5 px-3">{message.sender}</span>
                )}
                <div
                  className={`rounded-lg px-3 py-2 ${
                    message.isOwn ? "bg-[#d9fdd3] rounded-br-none" : "bg-white rounded-bl-none"
                  } shadow-sm`}
                >
                  <p className="text-sm text-gray-900 leading-relaxed">{message.content}</p>
                  <div className="flex items-center justify-end gap-1 mt-1">
                    <span className="text-xs text-gray-500">{message.timestamp}</span>
                    {message.isOwn && (
                      <svg className="w-4 h-4 text-blue-500" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M15.01 3.316l-.478-.372a.365.365 0 0 0-.51.063L8.666 9.879a.32.32 0 0 1-.484.033l-.358-.325a.319.319 0 0 0-.484.032l-.378.483a.418.418 0 0 0 .036.541l1.32 1.266c.143.14.361.125.484-.033l6.272-8.048a.366.366 0 0 0-.064-.512zm-4.1 0l-.478-.372a.365.365 0 0 0-.51.063L4.566 9.879a.32.32 0 0 1-.484.033L1.891 7.769a.366.366 0 0 0-.515.006l-.423.433a.364.364 0 0 0 .006.514l3.258 3.185c.143.14.361.125.484-.033l6.272-8.048a.365.365 0 0 0-.063-.51z" />
                      </svg>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Input Area */}
      <div
        className={`border-t border-gray-200 px-4 py-3 transition-all duration-300 ${
          isAIMode ? "bg-gradient-to-r from-purple-50 to-blue-50" : "bg-white"
        }`}
      >
        <div className="flex items-center gap-3">
          <div className="relative">
            <button
              onClick={() => setIsContentMenuOpen(!isContentMenuOpen)}
              className="w-9 h-9 rounded-full hover:bg-gray-100 flex items-center justify-center transition-colors flex-shrink-0"
            >
              <Plus className="w-6 h-6 text-gray-600" />
            </button>
          </div>
          {isContentMenuOpen && (
            <div className="absolute right-0 top-0 w-48 bg-white border border-gray-200 rounded-md shadow-lg py-1.5">
              <button
                onClick={() => setIsContentMenuOpen(false)}
                className="w-full px-4 py-2.5 hover:bg-gray-50 flex items-center gap-3 transition-colors text-left"
              >
                <ImageIcon className="w-5 h-5 text-yellow-600" />
                <span className="text-sm font-medium text-gray-900">Images</span>
              </button>

              <button
                onClick={() => setIsContentMenuOpen(false)}
                className="w-full px-4 py-2.5 hover:bg-gray-50 flex items-center gap-3 transition-colors text-left"
              >
                <Laugh className="w-5 h-5 text-orange-600" />
                <span className="text-sm font-medium text-gray-900">Memes</span>
              </button>

              <button
                onClick={() => setIsContentMenuOpen(false)}
                className="w-full px-4 py-2.5 hover:bg-gray-50 flex items-center gap-3 transition-colors text-left"
              >
                <BarChart3 className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-gray-900">Polls</span>
              </button>

              <button
                onClick={() => setIsContentMenuOpen(false)}
                className="w-full px-4 py-2.5 hover:bg-gray-50 flex items-center gap-3 transition-colors text-left"
              >
                <Calendar className="w-5 h-5 text-red-600" />
                <span className="text-sm font-medium text-gray-900">Events</span>
              </button>
            </div>
          )}
          <div className="flex-1 relative">
            <Input
              placeholder={isAIMode ? "Ask AI a question..." : "Message"}
              className={`bg-gray-100 border-0 rounded-full h-10 pr-10 focus-visible:ring-1 transition-all ${
                isAIMode
                  ? "bg-white border-2 border-purple-300 focus-visible:ring-purple-500"
                  : "focus-visible:ring-blue-500"
              }`}
            />
            <button className="absolute right-3 top-1/2 -translate-y-1/2 hover:opacity-70 transition-opacity">
              <Smile className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          <button
            onClick={() => setIsAIMode(!isAIMode)}
            className={`w-9 h-9 rounded-full flex items-center justify-center transition-all flex-shrink-0 ${
              isAIMode ? "bg-purple-600 hover:bg-purple-700 text-white" : "hover:bg-gray-100 text-purple-600"
            }`}
          >
            <Bot className="w-6 h-6" />
          </button>
        </div>
      </div>
    </div>
  )
}
