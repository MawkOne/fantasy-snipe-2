"use client"

import { useAuth } from "@/lib/auth-context"
import { useCallback } from "react"
import LoginModal from "@/components/login-modal"

export default function HeaderGate() {
  const { user } = useAuth()

  const handleClose = useCallback(() => {
    // Prevent closing the modal if user is not authenticated
    // Once logged in, modal can close normally
  }, [])

  return (
    <>
      <LoginModal isOpen={!user} onClose={handleClose} />
    </>
  )
}


