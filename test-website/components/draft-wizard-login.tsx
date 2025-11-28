"use client"

import type React from "react"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Eye, EyeOff } from "lucide-react"

export default function DraftWizardLogin() {
  const [showPassword, setShowPassword] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  const beginKindeLogin = () => {
    const domain = process.env.NEXT_PUBLIC_KINDE_DOMAIN
    const clientId = process.env.NEXT_PUBLIC_KINDE_CLIENT_ID
    const audience = process.env.NEXT_PUBLIC_KINDE_AUDIENCE
    const redirectUri = process.env.NEXT_PUBLIC_KINDE_REDIRECT_URI || `${window.location.origin}/callback`
    if (!domain || !clientId) {
      console.error("Kinde env vars missing: NEXT_PUBLIC_KINDE_DOMAIN / NEXT_PUBLIC_KINDE_CLIENT_ID")
      return
    }
    // Generate a strong state value (>= 8 chars) and persist for optional validation on callback
    let state = ""
    try {
      if (typeof crypto !== "undefined" && (crypto as any).getRandomValues) {
        const bytes = new Uint8Array(16)
        ;(crypto as any).getRandomValues(bytes)
        state = Array.from(bytes).map((b) => b.toString(16).padStart(2, "0")).join("")
      } else {
        state = Math.random().toString(36).slice(2) + Date.now().toString(36)
      }
      if (state.length < 8) state = state.padEnd(8, "0")
      try { sessionStorage.setItem("kinde_oauth_state", state) } catch {}
    } catch {}
    const url = `https://${domain}/oauth2/auth?client_id=${encodeURIComponent(String(clientId))}`
      + `&redirect_uri=${encodeURIComponent(String(redirectUri))}`
      + `&response_type=code&scope=openid%20profile%20email`
      + (audience ? `&audience=${encodeURIComponent(String(audience))}` : "")
      + `&state=${encodeURIComponent(state)}`
    // Public mode: skip Kinde and go straight to draft room
    window.location.href = "/draft-room-uhhp"
  }

  const handleSignIn = (e: React.FormEvent) => {
    e.preventDefault()
    window.location.href = "/draft-room-uhhp"
  }

  const handleGoogleSignIn = () => {
    beginKindeLogin()
  }

  const handleAppleSignIn = () => {
    beginKindeLogin()
  }

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Branding */}
      <div className="flex-1 bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center p-8">
        <div className="text-center">
          <div className="mb-8">
            <h1 className="text-6xl font-bold text-white mb-2">
              FantasySnipe<span className="text-orange-400">.ai</span>
            </h1>
            <div className="h-1 bg-orange-400 w-full rounded"></div>
          </div>
          <div className="text-white/80 text-xl max-w-md">
            <p className="mb-4">AI-Powered Draft Assistant</p>
            <p className="text-lg">
              Get intelligent draft recommendations, real-time player analysis, and strategic insights powered by
              advanced AI.
            </p>
          </div>
        </div>
      </div>

      {/* Right Side - Sign In Form */}
      <div className="w-96 bg-white flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <Card className="border-0 shadow-none">
            <CardHeader className="text-center pb-6">
              <CardTitle className="text-2xl font-bold text-gray-900">Sign In</CardTitle>
              <p className="text-gray-600 text-sm">
                Don't have an account?{" "}
                <Link href="/draft-wizard/signup" className="text-blue-600 hover:text-blue-800 font-medium">
                  Sign Up
                </Link>
              </p>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Social Sign In Buttons */}
              <Button
                variant="outline"
                className="w-full h-12 text-gray-700 border-gray-300 hover:bg-gray-50 bg-transparent"
                onClick={handleGoogleSignIn}
              >
                <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Continue with Google
              </Button>

              <Button
                variant="outline"
                className="w-full h-12 text-gray-700 border-gray-300 hover:bg-gray-50 bg-transparent"
                onClick={handleAppleSignIn}
              >
                <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z" />
                </svg>
                Continue with Apple
              </Button>

              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">OR</span>
                </div>
              </div>

              {/* Email/Password Form */}
              <form onSubmit={handleSignIn} className="space-y-4">
                <div>
                  <Label htmlFor="email" className="sr-only">
                    Email or Username
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Email or Username"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="h-12"
                    required
                  />
                </div>

                <div className="relative">
                  <Label htmlFor="password" className="sr-only">
                    Password
                  </Label>
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="h-12 pr-10"
                    required
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>

                <div className="text-right">
                  <Link href="/forgot-password" className="text-sm text-blue-600 hover:text-blue-800">
                    Forgot Password?
                  </Link>
                </div>

                <Button type="submit" className="w-full h-12 bg-blue-600 hover:bg-blue-700">
                  Sign In
                </Button>
              </form>

              {/* Terms */}
              <p className="text-xs text-gray-500 text-center mt-6">
                By clicking Sign In, you agree to our{" "}
                <Link href="/terms" className="text-blue-600 hover:text-blue-800">
                  Terms of Use
                </Link>{" "}
                and{" "}
                <Link href="/privacy" className="text-blue-600 hover:text-blue-800">
                  Privacy Policy
                </Link>
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
