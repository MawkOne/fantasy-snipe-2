"use client"

import { Button } from "@/components/ui/button"
import { X, Trophy } from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"

const DISMISS_KEY = "fs_sync_banner_dismissed_v1"

export default function HeroSection() {
  const [dismissed, setDismissed] = useState(true)

  useEffect(() => {
    const stored = typeof window !== "undefined" ? localStorage.getItem(DISMISS_KEY) : null
    setDismissed(stored === "1")
  }, [])

  const handleDismiss = () => {
    setDismissed(true)
    try {
      localStorage.setItem(DISMISS_KEY, "1")
    } catch {}
  }

  if (dismissed) return null

  return (
    <div className="bg-gradient-to-r from-[#0D47A1] to-[#1565C0] text-white">
      <div className="container mx-auto px-4 py-3 relative">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <Trophy className="w-5 h-5 shrink-0 text-white/90" aria-hidden="true" />
            <div className="min-w-0">
              <p className="font-semibold truncate">Sync your league for FREE!</p>
              <p className="text-sm text-white/80 truncate">Get personalized expert advice for your team</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link href="/sync">
              <Button size="sm" className="bg-white text-blue-700 hover:bg-white/90">
                Sync Your League
              </Button>
            </Link>
            <button
              onClick={handleDismiss}
              aria-label="Dismiss banner"
              className="rounded-full p-1.5 hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
