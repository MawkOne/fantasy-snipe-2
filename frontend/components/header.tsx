"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, X, User, LogOut } from "lucide-react"
import { useAuth } from "@/lib/auth-context"
import LoginModal from "@/components/login-modal"

export default function Header() {
  const [showPrivacyBanner, setShowPrivacyBanner] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const { user, teamMembership, logout } = useAuth()

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
              <Link href="/draft-wizard" className="hover:text-orange-400 transition-colors">
                Draft Wizard
              </Link>
              <Link href="/my-playbook" className="hover:text-orange-400 transition-colors">
                My Playbook
              </Link>
              <Link href="/rankings" className="hover:text-orange-400 transition-colors">
                Rankings
              </Link>
              <Link href="/research" className="hover:text-orange-400 transition-colors">
                Research
              </Link>
              <Link href="/dfs" className="hover:text-orange-400 transition-colors">
                DFS
              </Link>
            </nav>

            {/* Right Side */}
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search players..."
                  className="pl-10 w-48 bg-slate-800 border-slate-700 text-white"
                />
              </div>
              
              {user ? (
                <div className="flex items-center space-x-3">
                  {teamMembership && (
                    <div className="text-sm text-gray-300">
                      <span className="text-orange-400">{teamMembership.team_name}</span>
                    </div>
                  )}
                  <div className="flex items-center space-x-2">
                    <User className="w-4 h-4 text-gray-300" />
                    <span className="text-sm text-gray-300">{user?.email}</span>
                  </div>
                  <Button 
                    onClick={handleLogout} 
                    variant="outline" 
                    size="sm"
                    className="border-gray-600 text-gray-300 hover:bg-gray-800"
                  >
                    <LogOut className="w-4 h-4 mr-1" />
                    Logout
                  </Button>
                </div>
              ) : (
                <Button onClick={handleLogin} className="bg-orange-500 hover:bg-orange-600">
                  Get Started
                </Button>
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
