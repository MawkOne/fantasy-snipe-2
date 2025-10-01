"use client"

import { usePathname } from "next/navigation"
import Header from "@/components/header"

export default function HeaderGate() {
  const pathname = usePathname() || ""
  const hide = pathname.startsWith("/draft-room-uhhp")
  if (hide) return null
  return <Header />
}


