"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"

export default function CallbackPage() {
  const router = useRouter()

  useEffect(() => {
    // For now, just redirect to draft room
    // In a real implementation, you'd parse the auth code from the URL
    // and exchange it for tokens
    router.push("/draft-room-uhhp")
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
