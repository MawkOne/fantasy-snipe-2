"use client"

import {
  Search,
  MoreHorizontal,
  Smile,
  ArrowLeft,
  Bot,
  Sparkles,
  Calendar,
  BookOpen,
  BarChart3,
  Globe,
} from "lucide-react"
import { Input } from "@/components/ui/input"
import { useState } from "react"

interface AIChatViewProps {
  onBack?: () => void
}

export function AIChatView({ onBack }: AIChatViewProps) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: "AI",
      content:
        "Hi! I'm your League AI Assistant. I can help you organize events, clarify league rules, answer questions based on stats and data, and search for player status updates like injuries and game schedules. What would you like to know?",
      timestamp: "10:39 AM",
      isOwn: false,
    },
  ])

  const quickActions = [
    { icon: Calendar, label: "Organize Event", color: "text-blue-600", bg: "bg-white" },
    { icon: BookOpen, label: "League Rules", color: "text-green-600", bg: "bg-white" },
    { icon: BarChart3, label: "Stats & Research", color: "text-purple-600", bg: "bg-white" },
    { icon: Globe, label: "Player Status", color: "text-orange-600", bg: "bg-white" },
  ]

  return (
    <div className="flex-1 flex flex-col bg-gradient-to-br from-purple-100 via-indigo-50 to-blue-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {onBack && (
            <button
              onClick={onBack}
              className="md:hidden w-9 h-9 rounded-full hover:bg-gray-100 flex items-center justify-center transition-colors -ml-2"
            >
              <ArrowLeft className="w-5 h-5 text-gray-700" />
            </button>
          )}
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">League AI Assistant</h2>
            <p className="text-xs text-gray-500">Always active</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button className="hidden sm:flex w-9 h-9 rounded-full hover:bg-gray-100 items-center justify-center transition-colors">
            <Search className="w-5 h-5 text-gray-700" />
          </button>
          <button className="w-9 h-9 rounded-full hover:bg-gray-100 flex items-center justify-center transition-colors">
            <MoreHorizontal className="w-5 h-5 text-gray-700" />
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {/* Welcome Section */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center mb-4 shadow-lg">
            <Bot className="w-10 h-10 text-white" />
          </div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">League AI Assistant</h3>
          <p className="text-sm text-gray-600 text-center max-w-md mb-6">
            Your intelligent assistant for event planning, rule clarifications, stats research, and real-time player
            updates
          </p>

          {/* Quick Actions */}
          <div className="grid grid-cols-2 gap-3 w-full max-w-md mb-8">
            {quickActions.map((action, index) => (
              <button
                key={index}
                className={`${action.bg} ${action.color} rounded-xl p-4 hover:shadow-lg transition-all flex flex-col items-center gap-2 text-center shadow-md border border-gray-100`}
              >
                <action.icon className="w-6 h-6" />
                <span className="text-sm font-medium">{action.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Messages */}
        <div className="space-y-4 max-w-3xl mx-auto">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.isOwn ? "justify-end" : "justify-start"} gap-3`}>
              {!message.isOwn && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-white" />
                </div>
              )}
              <div className={`max-w-[75%] ${message.isOwn ? "items-end" : "items-start"} flex flex-col`}>
                <div
                  className={`rounded-2xl px-4 py-3 ${
                    message.isOwn
                      ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-none"
                      : "bg-white rounded-bl-none shadow-sm"
                  }`}
                >
                  <p className={`text-sm leading-relaxed ${message.isOwn ? "text-white" : "text-gray-900"}`}>
                    {message.content}
                  </p>
                  <div className="flex items-center justify-end gap-1 mt-1">
                    <span className={`text-xs ${message.isOwn ? "text-blue-100" : "text-gray-500"}`}>
                      {message.timestamp}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-4 py-3">
        <div className="flex items-center gap-2 max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <Input
              placeholder="Ask me anything about your fantasy league..."
              className="bg-gray-100 border-0 rounded-full h-11 pr-10 focus-visible:ring-2 focus-visible:ring-purple-500"
            />
            <button className="absolute right-3 top-1/2 -translate-y-1/2 hover:opacity-70 transition-opacity">
              <Smile className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          <button className="w-11 h-11 rounded-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 flex items-center justify-center transition-all shadow-md flex-shrink-0">
            <Sparkles className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>
    </div>
  )
}
