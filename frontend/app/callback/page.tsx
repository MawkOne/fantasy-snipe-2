"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { useAuth } from "@/lib/auth-context"

export default function CallbackPage() {
  const router = useRouter()
  const { login } = useAuth()

  useEffect(() => {
    async function handle() {
      try {
        const params = new URLSearchParams(window.location.search)
        const code = params.get("code") || ""
        if (!code) {
          router.replace("/login")
          return
        }
        // Do not hard-fail on state mismatch to avoid redirect loops in some browsers
        const redirectUri = `${window.location.origin}/callback`
        const res = await fetch("/api/auth/token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code, redirectUri }),
          cache: "no-store",
          credentials: "omit",
        })
        if (!res.ok) {
          router.replace("/login")
          return
        }
        const data = await res.json()
        const email = data?.profile?.email || data?.tokens?.user_info?.email || ""
        const name = data?.profile?.name || data?.tokens?.user_info?.name || ""
        if (email) {
          login(email, name)
          router.replace("/draft-room-uhhp")
        } else {
          router.replace("/login")
        }
      } catch {
        router.replace("/login")
      }
    }
    handle()
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-4"></div>
        <p className="text-gray-600">Completing authentication...</p>
      </div>
    </div>
  )
}
