"use client"

import { useAuth } from "@/hooks/use-auth"
import { AuthModal } from "@/components/auth-modal"
import { useState, useEffect } from "react"
import { Loader2 } from "lucide-react"

interface AuthGateProps {
  children: React.ReactNode
}

export function AuthGate({ children }: AuthGateProps) {
  const { user, loading } = useAuth()
  const [showAuthModal, setShowAuthModal] = useState(false)

  // Show auth modal once we know user is not logged in
  useEffect(() => {
    if (!loading && !user) {
      setShowAuthModal(true)
    }
  }, [loading, user])

  // Loading state - checking authentication
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-[#36393F]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  // Not authenticated - show auth modal
  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center max-w-md px-6">
          <div className="mb-8">
            <img 
              src="/pool-logo.jpeg" 
              alt="UHHP Logo" 
              className="w-24 h-24 rounded-full mx-auto mb-6 shadow-lg"
            />
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-3">
              UHHP Fantasy Chat
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-300">
              Welcome to your fantasy league chat and management platform
            </p>
          </div>

          <AuthModal 
            open={showAuthModal} 
            onClose={() => {}} // Don't allow closing - must authenticate
            onSuccess={() => {
              setShowAuthModal(false)
              // User state will update automatically via useAuth
            }}
          />
        </div>
      </div>
    )
  }

  // Authenticated - show app
  return <>{children}</>
}

