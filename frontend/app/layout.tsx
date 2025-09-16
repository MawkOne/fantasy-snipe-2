import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import AuthProviderWrapper from "@/components/auth-provider-wrapper"
import HeaderGate from "@/components/header-gate"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "FantasySnipe.ai - AI-Powered Fantasy Hockey Rankings & Draft Tools",
  description:
    "The ultimate AI-powered fantasy hockey platform with expert rankings, draft tools, and personalized advice.",
    generator: 'v0.app'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProviderWrapper>
          <HeaderGate />
          {children}
        </AuthProviderWrapper>
      </body>
    </html>
  )
}
