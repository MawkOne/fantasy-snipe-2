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
  Send,
  Sparkles,
} from "lucide-react"
import { Input } from "@/components/ui/input"
import { useState, useRef, useEffect } from "react"
import { useMessages } from "@/hooks/use-messages"
import { useAIAssistant } from "@/hooks/use-ai-assistant"
import { getSuggestedQuestions } from "@/lib/ai-assistant"
import { useAuth } from "@/hooks/use-auth"

interface ChatViewProps {
  onBack?: () => void
}

export function ChatView({ onBack }: ChatViewProps) {
  const { user } = useAuth()

  // Get current user from Firebase Auth
  // User will always exist here because of AuthGate
  const CURRENT_USER = {
    id: user?.uid || "unknown",
    name: user?.displayName || "User",
    avatar: user?.photoURL || "/placeholder-user.jpg",
  }
  const [isContentMenuOpen, setIsContentMenuOpen] = useState(false)
  const [isAIMode, setIsAIMode] = useState(false)
  const [messageText, setMessageText] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Connect to Firebase - "general-chat" is the chat room ID
  const { messages: firebaseMessages, loading, sendMessage } = useMessages("general-chat")
  
  // AI Assistant
  const { messages: aiMessages, isLoading: aiLoading, askQuestion } = useAIAssistant()
  const [suggestedQuestions] = useState(getSuggestedQuestions())

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [firebaseMessages, aiMessages, aiLoading])

  // Format Firebase timestamp to display time
  const formatTime = (timestamp: any) => {
    if (!timestamp) return ""
    const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp)
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    })
  }

  // Send a message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!messageText.trim()) return

    const textToSend = messageText.trim()
    setMessageText("") // Clear immediately before sending

    if (isAIMode) {
      // Ask AI
      await askQuestion(textToSend)
    } else {
      // Send to Firebase chat
      await sendMessage(textToSend, CURRENT_USER.id, CURRENT_USER.name, CURRENT_USER.avatar)
    }
  }

  // Handle suggested question click
  const handleSuggestedQuestion = async (question: string) => {
    await askQuestion(question)
  }

  // Convert messages to display format
  const displayMessages = isAIMode 
    ? aiMessages.map((msg, idx) => ({
        id: `ai-${idx}`,
        sender: msg.role === "user" ? CURRENT_USER.name : "AI Assistant",
        content: msg.content,
        timestamp: new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true }),
        isOwn: msg.role === "user",
        avatar: msg.role === "user" ? CURRENT_USER.avatar : "/pool-logo.jpeg",
      }))
    : firebaseMessages.map((msg) => ({
        id: msg.id,
        sender: msg.userName,
        content: msg.text,
        timestamp: formatTime(msg.timestamp),
        isOwn: msg.userId === CURRENT_USER.id,
        avatar: msg.userAvatar || "/placeholder.svg",
      }))

  return (
    <div className="flex-1 flex flex-col bg-[#f0ebe3] dark:bg-[#36393F] transition-colors duration-300">
      {/* Header */}
      <div className="bg-white dark:bg-[#2f3136] border-b border-gray-200 dark:border-[#202225] px-6 py-3 flex items-center justify-between gap-4 transition-colors duration-300">
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
            <h2 className="font-semibold text-gray-900 dark:text-gray-100">Henderson's</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">Don, Rob, You</p>
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
      <div className="flex-1 min-h-0 overflow-y-auto px-6 py-4 bg-gray-50 dark:bg-[#36393F]">
        {/* Date Separator */}
        <div className="flex justify-center mb-6">
          <div className="bg-white dark:bg-[#40444b] px-4 py-1.5 rounded-full shadow-sm">
            <span className="text-xs font-medium text-gray-700 dark:text-gray-200">Today</span>
          </div>
        </div>

            {/* Loading State */}
            {(loading || aiLoading) && displayMessages.length === 0 && (
              <div className="flex justify-center items-center h-32">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {isAIMode ? "AI is thinking..." : "Loading messages..."}
                </p>
              </div>
            )}

            {/* Empty State */}
            {!loading && !aiLoading && displayMessages.length === 0 && (
              <div className="flex flex-col justify-center items-center h-32 text-center">
                {isAIMode ? (
                  <>
                    <Sparkles className="w-12 h-12 text-purple-500 mb-3" />
                    <p className="text-sm text-gray-700 dark:text-gray-200 font-medium mb-1">AI Assistant Mode</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">Ask me anything about NHL players or fantasy hockey!</p>
                    
                    {/* Suggested Questions */}
                    <div className="grid grid-cols-1 gap-2 w-full max-w-md px-4">
                      {suggestedQuestions.slice(0, 4).map((question, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSuggestedQuestion(question)}
                          className="text-xs text-left px-3 py-2 bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/30 rounded-lg border border-purple-200 dark:border-purple-700 text-purple-700 dark:text-purple-300 transition-colors"
                        >
                          💡 {question}
                        </button>
                      ))}
                    </div>
                  </>
                ) : (
                  <>
                    <p className="text-sm text-gray-700 dark:text-gray-200 font-medium mb-1">No messages yet</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Be the first to send a message!</p>
                  </>
                )}
              </div>
            )}

        {/* Messages */}
        <div className="space-y-2">
          {displayMessages.map((message) => (
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
                    message.isOwn 
                      ? "bg-[#d9fdd3] dark:bg-teal-600 rounded-br-none" 
                      : "bg-white dark:bg-[#40444b] rounded-bl-none"
                  } shadow-sm`}
                >
                  <p className="text-sm text-gray-900 dark:text-white leading-relaxed">{message.content}</p>
                  <div className="flex items-center justify-end gap-1 mt-1">
                    <span className="text-xs text-gray-500 dark:text-gray-300">{message.timestamp}</span>
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

          {/* AI Loading Indicator - Shows AFTER messages */}
          {aiLoading && displayMessages.length > 0 && (
            <div className="flex justify-start gap-2">
              <img src="/pool-logo.jpeg" alt="AI" className="w-8 h-8 rounded-full object-cover flex-shrink-0 mt-1" />
              <div className="max-w-[65%] items-start flex flex-col">
                <span className="text-xs font-medium text-purple-600 dark:text-purple-400 mb-0.5 px-3">AI Assistant</span>
                <div className="rounded-lg px-3 py-2 bg-white dark:bg-[#40444b] rounded-bl-none shadow-sm">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div
        className={`border-t border-gray-200 dark:border-[#202225] px-4 py-3 transition-all duration-300 ${
          isAIMode 
            ? "bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20" 
            : "bg-white dark:bg-[#40444b]"
        }`}
      >
        <div className="flex items-center gap-3">
          <div className="relative">
            <button
              onClick={() => setIsContentMenuOpen(!isContentMenuOpen)}
              className="w-9 h-9 rounded-full hover:bg-gray-100 dark:hover:bg-[#2f3136] flex items-center justify-center transition-colors flex-shrink-0"
            >
              <Plus className="w-6 h-6 text-gray-600 dark:text-gray-300" />
            </button>
          {isContentMenuOpen && (
              <div className="absolute left-0 bottom-full mb-2 w-56 bg-white dark:bg-[#2f3136] border border-gray-200 dark:border-[#202225] rounded-lg shadow-lg py-2 z-50">
              <button
                onClick={() => setIsContentMenuOpen(false)}
                  className="w-full px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-[#40444b] flex items-center gap-3 transition-colors text-left"
              >
                  <ImageIcon className="w-5 h-5 text-yellow-600 dark:text-yellow-500" />
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Images</span>
              </button>

              <button
                onClick={() => setIsContentMenuOpen(false)}
                  className="w-full px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-[#40444b] flex items-center gap-3 transition-colors text-left"
              >
                  <Laugh className="w-5 h-5 text-orange-600 dark:text-orange-500" />
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Memes</span>
              </button>

              <button
                onClick={() => setIsContentMenuOpen(false)}
                  className="w-full px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-[#40444b] flex items-center gap-3 transition-colors text-left"
              >
                  <BarChart3 className="w-5 h-5 text-green-600 dark:text-green-500" />
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Polls</span>
              </button>

              <button
                onClick={() => setIsContentMenuOpen(false)}
                  className="w-full px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-[#40444b] flex items-center gap-3 transition-colors text-left"
              >
                  <Calendar className="w-5 h-5 text-red-600 dark:text-red-500" />
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Events</span>
              </button>
            </div>
          )}
          </div>
          <form onSubmit={handleSendMessage} className="flex-1 relative">
            <Input
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              placeholder={isAIMode ? "Ask AI a question..." : "Message"}
              className={`bg-gray-100 dark:bg-[#40444b] dark:text-gray-100 dark:placeholder:text-gray-400 border-0 rounded-full h-10 pr-20 focus-visible:ring-1 transition-all ${
                isAIMode
                  ? "bg-white dark:bg-[#40444b] border-2 border-purple-300 dark:border-purple-600 focus-visible:ring-purple-500"
                  : "focus-visible:ring-blue-500"
              }`}
            />
            <button
              type="button"
              className="absolute right-12 top-1/2 -translate-y-1/2 hover:opacity-70 transition-opacity"
            >
              <Smile className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            </button>
            <button
              type="submit"
              disabled={!messageText.trim()}
              className="absolute right-3 top-1/2 -translate-y-1/2 disabled:opacity-30 transition-opacity"
            >
              <Send className="w-5 h-5 text-blue-500 dark:text-blue-400" />
            </button>
          </form>

          <button
            onClick={() => setIsAIMode(!isAIMode)}
            className={`w-9 h-9 rounded-full flex items-center justify-center transition-all flex-shrink-0 ${
              isAIMode 
                ? "bg-purple-600 hover:bg-purple-700 text-white" 
                : "hover:bg-gray-100 dark:hover:bg-[#2f3136] text-purple-600 dark:text-purple-400"
            }`}
          >
            <Bot className="w-6 h-6" />
          </button>
        </div>
      </div>
    </div>
  )
}
