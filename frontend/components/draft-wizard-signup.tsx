"use client"

import type React from "react"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Eye, EyeOff } from "lucide-react"

export default function DraftWizardSignup() {
  const [showPassword, setShowPassword] = useState(false)
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    confirmPassword: "",
  })

  const handleSignUp = (e: React.FormEvent) => {
    e.preventDefault()
    // Handle sign up logic here
    console.log("Sign up with:", formData)
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
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
            <p className="mb-4">Join the AI Revolution</p>
            <p className="text-lg">
              Create your account and start dominating your fantasy hockey drafts with cutting-edge AI technology.
            </p>
          </div>
        </div>
      </div>

      {/* Right Side - Sign Up Form */}
      <div className="w-96 bg-white flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <Card className="border-0 shadow-none">
            <CardHeader className="text-center pb-6">
              <CardTitle className="text-2xl font-bold text-gray-900">Create Account</CardTitle>
              <p className="text-gray-600 text-sm">
                Already have an account?{" "}
                <Link href="/draft-wizard" className="text-blue-600 hover:text-blue-800 font-medium">
                  Sign In
                </Link>
              </p>
            </CardHeader>

            <CardContent>
              <form onSubmit={handleSignUp} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="firstName" className="sr-only">
                      First Name
                    </Label>
                    <Input
                      id="firstName"
                      type="text"
                      placeholder="First Name"
                      value={formData.firstName}
                      onChange={(e) => handleInputChange("firstName", e.target.value)}
                      className="h-12"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="lastName" className="sr-only">
                      Last Name
                    </Label>
                    <Input
                      id="lastName"
                      type="text"
                      placeholder="Last Name"
                      value={formData.lastName}
                      onChange={(e) => handleInputChange("lastName", e.target.value)}
                      className="h-12"
                      required
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="email" className="sr-only">
                    Email
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Email Address"
                    value={formData.email}
                    onChange={(e) => handleInputChange("email", e.target.value)}
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
                    value={formData.password}
                    onChange={(e) => handleInputChange("password", e.target.value)}
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

                <div>
                  <Label htmlFor="confirmPassword" className="sr-only">
                    Confirm Password
                  </Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="Confirm Password"
                    value={formData.confirmPassword}
                    onChange={(e) => handleInputChange("confirmPassword", e.target.value)}
                    className="h-12"
                    required
                  />
                </div>

                <Button type="submit" className="w-full h-12 bg-blue-600 hover:bg-blue-700">
                  Create Account
                </Button>
              </form>

              {/* Terms */}
              <p className="text-xs text-gray-500 text-center mt-6">
                By creating an account, you agree to our{" "}
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
