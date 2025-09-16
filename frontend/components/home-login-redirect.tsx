"use client"

import { useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useAuth } from "@/lib/auth-context"

export default function HomeLoginRedirect() {
  const { user } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (user && pathname === "/") {
      router.replace("/draft-room-uhhp")
    }
  }, [user, pathname, router])

  return null
}
