"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"
import Link from "next/link"
import { useState } from "react"

export default function WhoShouldIDraftCard() {
  const [p1, setP1] = useState("")
  const [p2, setP2] = useState("")

  const popular = ["McDavid or Draisaitl", "MacKinnon or Pastrnak", "Matthews or Kucherov", "Rantanen or Kaprizov"]

  return (
    <Card className="rounded-2xl">
      <CardHeader>
        <CardTitle className="text-base text-gray-900">Who Should I Draft</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" aria-hidden="true" />
            <Input
              placeholder="Enter First Player"
              value={p1}
              onChange={(e) => setP1(e.target.value)}
              className="pl-9"
              aria-label="First player"
            />
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" aria-hidden="true" />
            <Input
              placeholder="Enter Second Player"
              value={p2}
              onChange={(e) => setP2(e.target.value)}
              className="pl-9"
              aria-label="Second player"
            />
          </div>
          <Link href={`/compare/${encodeURIComponent((p1 || "player-a") + "-vs-" + (p2 || "player-b"))}`}>
            <Button className="w-full bg-blue-600 hover:bg-blue-700">See Advice</Button>
          </Link>
        </div>

        <div className="pt-1">
          <p className="text-xs font-semibold text-gray-500 uppercase">Popular Searches</p>
          <ul className="mt-2 space-y-1.5">
            {popular.map((term) => (
              <li key={term}>
                <Link
                  href={`/compare/${term.toLowerCase().replace(/\s+/g, "-")}`}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  {term}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}
