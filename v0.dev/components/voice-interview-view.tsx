"use client"

import { useState, useEffect } from "react"
import { ArrowLeft, Share2, MoreHorizontal, X } from "lucide-react"
import { Button } from "@/components/ui/button"

interface VoiceInterviewViewProps {
  onBack?: () => void
  interviewTitle?: string
}

export function VoiceInterviewView({ onBack, interviewTitle = "Weekly Podcast Interview" }: VoiceInterviewViewProps) {
  const [isListening, setIsListening] = useState(true)
  const [seconds, setSeconds] = useState(0)
  const [audioLevel, setAudioLevel] = useState(0.5)

  useEffect(() => {
    if (isListening) {
      const timer = setInterval(() => {
        setSeconds((prev) => prev + 1)
      }, 1000)
      return () => clearInterval(timer)
    }
  }, [isListening])

  useEffect(() => {
    // Simulate audio level changes
    const audioTimer = setInterval(() => {
      setAudioLevel(Math.random())
    }, 100)
    return () => clearInterval(audioTimer)
  }, [])

  const formatTime = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60)
    const secs = totalSeconds % 60
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  const handleEndConversation = () => {
    setIsListening(false)
    if (onBack) {
      onBack()
    }
  }

  return (
    <div className="flex-1 flex flex-col bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <div className="bg-gray-900/50 backdrop-blur-sm border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <button
            onClick={onBack}
            className="w-10 h-10 rounded-full hover:bg-gray-700/50 flex items-center justify-center transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-300" />
          </button>

          <div className="flex items-center gap-3">
            <button className="px-4 py-2 bg-gray-700/50 hover:bg-gray-700 rounded-full flex items-center gap-2 transition-colors">
              <Share2 className="w-4 h-4 text-gray-300" />
              <span className="text-sm text-gray-300">Share Agent</span>
            </button>
            <button className="w-10 h-10 rounded-full hover:bg-gray-700/50 flex items-center justify-center transition-colors">
              <MoreHorizontal className="w-5 h-5 text-gray-300" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-between p-8">
        {/* Top Section */}
        <div className="w-full max-w-2xl space-y-6">
          {/* Agent Info */}
          <div className="flex items-center gap-4">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <img src="/pool-logo.jpeg" alt="Agent" className="w-16 h-16 rounded-xl object-cover" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">{interviewTitle}</h1>
              <p className="text-gray-400 text-sm mt-1">Fantasy League Press</p>
            </div>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-6 text-gray-400 text-sm">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              <span>1 conversation</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>{formatTime(seconds)} spoken</span>
            </div>
          </div>

          {/* Conversation ID */}
          <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
            <p className="text-gray-400 text-sm mb-2">Conversation ID</p>
            <p className="text-gray-300 font-mono text-sm">vZJL2Ixfo3NX9nze2et0</p>
          </div>
        </div>

        {/* Audio Visualization */}
        <div className="flex flex-col items-center justify-center flex-1">
          <div className="relative w-80 h-80">
            {/* Outer circles */}
            <div className="absolute inset-0 rounded-full border border-gray-700/30" />
            <div className="absolute inset-8 rounded-full border border-gray-700/30" />
            <div className="absolute inset-16 rounded-full border border-gray-700/30" />

            {/* Animated dots */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="relative w-64 h-64">
                {Array.from({ length: 40 }).map((_, i) => {
                  const angle = (i / 40) * Math.PI * 2
                  const radius = 100 + Math.sin(Date.now() / 1000 + i) * 20
                  const x = Math.cos(angle) * radius
                  const y = Math.sin(angle) * radius
                  const isActive = i >= 10 && i <= 30
                  return (
                    <div
                      key={i}
                      className={`absolute w-2 h-2 rounded-full transition-all duration-300 ${
                        isActive ? "bg-green-500" : "bg-gray-600"
                      }`}
                      style={{
                        left: `calc(50% + ${x}px)`,
                        top: `calc(50% + ${y}px)`,
                        transform: "translate(-50%, -50%)",
                        opacity: isActive ? 0.8 + audioLevel * 0.2 : 0.3,
                      }}
                    />
                  )
                })}
              </div>
            </div>

            {/* Center icon */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-16 h-16 rounded-full bg-gray-800 border-2 border-gray-700 flex items-center justify-center">
                <img src="/pool-logo.jpeg" alt="Agent" className="w-12 h-12 rounded-full object-cover" />
              </div>
            </div>
          </div>

          {/* Status */}
          <div className="mt-8 text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
              <p className="text-gray-400 text-sm">listening...</p>
            </div>
            <p className="text-white text-3xl font-semibold">{formatTime(seconds)}</p>
          </div>
        </div>

        {/* End Button */}
        <div className="w-full max-w-md">
          <Button
            onClick={handleEndConversation}
            className="w-full bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white py-6 rounded-full text-lg font-medium flex items-center justify-center gap-2"
          >
            <X className="w-5 h-5" />
            End Conversation
          </Button>
        </div>
      </div>
    </div>
  )
}
