"use client"

import { useAuth } from "@/lib/auth-context"
import { useEffect } from "react"
import { usePathname, useRouter } from "next/navigation"

// Redirect to /login whenever user is not authenticated.
// Allow the login and callback routes to remain accessible.
export default function HeaderGate() {
  const { user } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!user) {
      const safePaths = new Set(["/login", "/callback", "/draft-wizard/signup"]) // add more public routes if needed
      if (!safePaths.has(pathname || "")) {
        router.replace("/login")
      }
    }
  }, [user, pathname, router])

  return null
}


