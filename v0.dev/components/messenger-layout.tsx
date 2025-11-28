"use client"

import { useState } from "react"
import { AuthGate } from "./auth-gate"
import { LeaguesSidebar } from "./leagues-sidebar"
import { ChatsSidebar } from "./chats-sidebar"
import { ChatView } from "./chat-view"
import { AIChatView } from "./ai-chat-view"
import { PressRequestsView } from "./press-requests-view"
import { ProfileSettingsView } from "./profile-settings-view"
import { RosterView } from "./roster-view"
import { PodcastEpisodesSidebar } from "./podcast-episodes-sidebar"
import { PodcastPlayerView } from "./podcast-player-view"
import { VoiceInterviewView } from "./voice-interview-view"

export type MobileView = "leagues" | "chats" | "messages"
export type ChatType =
  | "general"
  | "ai"
  | "press"
  | "profile"
  | "roster"
  | "member"
  | "podcast"
  | "voice-interview"
  | null

export function MessengerLayout() {
  const [mobileView, setMobileView] = useState<MobileView>("chats")
  const [activeChatType, setActiveChatType] = useState<ChatType>(null)
  const [selectedEpisodeId, setSelectedEpisodeId] = useState<number | null>(null)

  const handleOpenVoiceInterview = () => {
    setActiveChatType("voice-interview")
    setMobileView("messages")
  }

  return (
    <AuthGate>
    <div className="flex h-screen bg-white dark:bg-[#202225] overflow-hidden transition-colors duration-300">
      <div className={`${mobileView === "messages" ? "hidden" : "flex"} lg:flex`}>
        <LeaguesSidebar
          activeChatType={activeChatType}
          onNavigate={() => setMobileView("chats")}
          onOpenChat={() => {
            setActiveChatType(null)
            setSelectedEpisodeId(null)
            setMobileView("chats")
          }}
          onOpenPodcast={() => {
            const isMobile = typeof window !== "undefined" && window.innerWidth < 768
            setActiveChatType("podcast")
            setSelectedEpisodeId(isMobile ? null : 1)
            setMobileView(isMobile ? "chats" : "messages")
          }}
        />
      </div>

      <div
        className={`${mobileView === "messages" ? "hidden" : "flex"} md:flex ${activeChatType ? "md:flex lg:flex" : ""}`}
      >
        {activeChatType === "podcast" ? (
          <PodcastEpisodesSidebar
            onBack={() => {
              setActiveChatType(null)
              setMobileView("chats")
            }}
            onSelectEpisode={(episodeId) => {
              setSelectedEpisodeId(episodeId)
              setMobileView("messages")
            }}
          />
        ) : (
          <ChatsSidebar
            onOpenChat={() => {
              setActiveChatType("general")
              setMobileView("messages")
            }}
            onOpenAIChat={() => {
              setActiveChatType("ai")
              setMobileView("messages")
            }}
            onOpenPressRequests={() => {
              setActiveChatType("press")
              setMobileView("messages")
            }}
            onOpenProfile={() => {
              setActiveChatType("profile")
              setMobileView("messages")
            }}
            onOpenRoster={() => {
              setActiveChatType("roster")
              setMobileView("messages")
            }}
            onOpenMemberChat={() => {
              setActiveChatType("member")
              setMobileView("messages")
            }}
            onOpenLeagues={() => setMobileView("leagues")}
          />
        )}
      </div>

      {/* Chat Views - Show appropriate chat based on activeChatType */}
      <div className={`${activeChatType || mobileView === "messages" ? "flex" : "hidden"} md:flex flex-1`}>
        {activeChatType === "voice-interview" ? (
          <VoiceInterviewView
            onBack={() => {
              setActiveChatType("press")
              setMobileView("messages")
            }}
          />
        ) : activeChatType === "podcast" && selectedEpisodeId ? (
          <PodcastPlayerView
            episodeId={selectedEpisodeId}
            onBack={() => {
              setSelectedEpisodeId(null)
              setMobileView("chats")
            }}
          />
        ) : activeChatType === "ai" ? (
          <AIChatView
            onBack={() => {
              setActiveChatType(null)
              setMobileView("chats")
            }}
          />
        ) : activeChatType === "press" ? (
          <PressRequestsView
            onBack={() => {
              setActiveChatType(null)
              setMobileView("chats")
            }}
            onOpenVoiceInterview={handleOpenVoiceInterview}
          />
        ) : activeChatType === "roster" ? (
          <RosterView
            onBack={() => {
              setActiveChatType(null)
              setMobileView("chats")
            }}
          />
        ) : activeChatType === "profile" ? (
          <ProfileSettingsView
            onBack={() => {
              setActiveChatType(null)
              setMobileView("chats")
            }}
          />
        ) : (
          <ChatView
            onBack={() => {
              setActiveChatType(null)
              setMobileView("chats")
            }}
          />
        )}
      </div>
    </div>
    </AuthGate>
  )
}
