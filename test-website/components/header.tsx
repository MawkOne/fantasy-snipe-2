"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { X } from "lucide-react"

export default function Header() {
  const [showPrivacyBanner, setShowPrivacyBanner] = useState(false)

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
    </>
  )
}