"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { X, User, LogOut } from "lucide-react"
import { useAuth } from "@/lib/auth-context"
import LoginModal from "@/components/login-modal"

export default function Header() {
  const [showPrivacyBanner, setShowPrivacyBanner] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const { user, teamMembership, logout } = useAuth()
  const syncHref = user ? "/sync" : "/login"

  useEffect(() => {
    // Check if user has already accepted terms
    const hasAccepted = localStorage.getItem("termsAccepted")
    if (!hasAccepted) {
      setShowPrivacyBanner(true)
    }
  }, [])

  const handleAcceptTerms = () => {
    localStorage.setItem("termsAccepted", "true")
    setShowPrivacyBanner(false)
  }

  const handleDismiss = () => {
    setShowPrivacyBanner(false)
  }

  const handleLogin = () => {
    setShowLoginModal(true)
  }

  const handleLogout = () => {
    logout()
  }

  return (
    <>
      {/* Privacy Notice Banner */}
      {showPrivacyBanner && (
        <div className="bg-blue-600 text-white text-center py-3 px-4 relative">
          <div className="max-w-4xl mx-auto flex items-center justify-center space-x-4">
            <p className="text-sm">
              By accessing this site you agree to our{" "}
              <Link href="/privacy-policy" className="underline hover:text-blue-200">
                Privacy Policy
              </Link>{" "}
              and{" "}
              <Link href="/terms-of-use" className="underline hover:text-blue-200">
                Terms of Use
              </Link>
              .
            </p>
            <div className="flex items-center space-x-2">
              <Button
                onClick={handleAcceptTerms}
                variant="secondary"
                size="sm"
                className="bg-white text-blue-600 hover:bg-gray-100 text-xs px-4 py-1"
              >
                Accept
              </Button>
              <button
                onClick={handleDismiss}
                className="text-white hover:text-blue-200 p-1"
                aria-label="Dismiss banner"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Header */}
      <header className="bg-slate-900 text-white">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link href="/" className="text-2xl font-bold text-orange-400">
              FantasySnipe.ai
            </Link>

            {/* Navigation */}
            <nav className="hidden md:flex items-center space-x-6">
              <Link href="/my-playbook" className="hover:text-orange-400 transition-colors">
                My Playbook
              </Link>
              <Link href="/research" className="hover:text-orange-400 transition-colors">
                Research
              </Link>
              <Link href="/podcast" className="hover:text-orange-400 transition-colors">
                Snipe Podcast
              </Link>
              <Link href="/chat" className="hover:text-orange-400 transition-colors">
                Snipe Chat
              </Link>
            </nav>

            {/* Right Side */}
            <div className="flex items-center space-x-4">
              <Link href={syncHref}>
                <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                  Sync League
                </Button>
              </Link>

              {user ? (
                <div className="flex items-center space-x-3">
                  <Link href="/account">
                    <User className="w-5 h-5 text-gray-300 hover:text-white" />
                  </Link>
                </div>
              ) : (
                <Link href="/login">
                  <Button className="bg-orange-500 hover:bg-orange-600">
                    Get Started
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Login Modal */}
      <LoginModal 
        isOpen={showLoginModal} 
        onClose={() => setShowLoginModal(false)} 
      />
    </>
  )
}
