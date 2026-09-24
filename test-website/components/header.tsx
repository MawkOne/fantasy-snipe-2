"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { LogOut, User, X } from "lucide-react"
import { useAuth } from "@/lib/auth-context"
import LoginModal from "@/components/login-modal"

export default function Header() {
  const [showPrivacyBanner, setShowPrivacyBanner] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const { user, logout } = useAuth()

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

      <header className="h-14 border-b border-slate-800 bg-slate-900 text-white">
        <div className="mx-auto flex h-full max-w-screen-2xl items-center justify-end gap-2 px-4">
          {user ? (
            <>
              <Link href="/account">
                <Button variant="ghost" size="sm" className="text-slate-200 hover:bg-slate-800 hover:text-white">
                  <User className="mr-2 h-4 w-4" />
                  Account
                </Button>
              </Link>
              <Button
                variant="ghost"
                size="sm"
                className="text-slate-200 hover:bg-slate-800 hover:text-white"
                onClick={() => logout()}
              >
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </Button>
            </>
          ) : (
            <Button size="sm" className="bg-orange-500 hover:bg-orange-600" onClick={() => setShowLoginModal(true)}>
              Login
            </Button>
          )}
        </div>
      </header>

      <LoginModal isOpen={showLoginModal} onClose={() => setShowLoginModal(false)} />
    </>
  )
}