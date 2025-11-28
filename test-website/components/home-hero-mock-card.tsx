import Image from "next/image"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Star } from "lucide-react"
import Link from "next/link"

const players = [
  {
    name: "Chase Brown",
    team: "CIN (Bye 10)",
    role: "RB",
    percent: 43,
    overall: 18,
    ecr: 20,
    image: "/hockey-player-headshot.png",
  },
  {
    name: "Garrett Wilson",
    team: "NYJ (Bye 9)",
    role: "WR",
    percent: 36,
    overall: 23,
    ecr: 21,
    image: "/hockey-player-headshot.png",
  },
  {
    name: "Alvin Kamara",
    team: "NO (Bye 11)",
    role: "RB",
    percent: 22,
    overall: 31,
    ecr: 34,
    image: "/hockey-player-headshot.png",
  },
]

export default function HomeHeroMockCard() {
  return (
    <Card className="overflow-hidden rounded-2xl border border-orange-200/50 shadow-sm">
      <div className="relative isolate grid gap-0 md:grid-cols-[1fr_360px]">
        {/* Orange gradient panel */}
        <div className="bg-gradient-to-br from-orange-400 via-orange-500 to-orange-600 p-6 md:p-8 text-white">
          <div className="max-w-xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-medium backdrop-blur">
              <Star className="h-3.5 w-3.5" />
              Featured
            </div>
            <h1 className="mt-3 text-3xl md:text-4xl font-extrabold tracking-tight">Practice Makes Playoffs</h1>
            <p className="mt-2 text-white/90">
              Fast, free mock drafts against realistic opponents. Test strategies, draft from any position, and get
              instant grades.
            </p>
            <div className="mt-5">
              <Link href="/draft-wizard/mock-draft-simulator">
                <Button size="lg" className="bg-yellow-300 text-black hover:bg-yellow-200 font-semibold">
                  Start a Mock
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Right stacked mini-cards */}
        <div className="hidden md:flex flex-col gap-3 bg-gradient-to-b from-orange-50 to-white p-6">
          {players.map((p, idx) => (
            <div
              key={idx}
              className="flex items-center gap-3 rounded-xl border border-orange-200 bg-white/90 p-3 shadow-sm"
            >
              <Image
                src={p.image || "/placeholder.svg"}
                alt={p.name}
                width={44}
                height={44}
                className="rounded-full object-cover"
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium truncate">{p.name}</p>
                  <span className="text-emerald-600 text-sm font-semibold">{p.percent}%</span>
                </div>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center rounded-md bg-blue-50 px-1.5 py-0.5 font-semibold text-blue-700">
                      {p.role}
                    </span>
                    <span className="truncate">{p.team}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600">Overall {p.overall}</span>
                    <span className="text-gray-400">ECR {p.ecr}</span>
                  </div>
                </div>
              </div>
              <Link href="/draft-wizard/mock-draft-simulator">
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                  Draft
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </div>

      {/* Article teaser under hero */}
      <div className="border-t bg-white p-5 md:p-6">
        <h2 className="text-xl md:text-2xl font-bold">Fast, Free Mock Drafts</h2>
        <p className="text-sm text-gray-500 mt-1">
          by <span className="text-blue-600">FantasySnipe.ai Staff</span> | August 2, 2025
        </p>
        <p className="mt-2 text-gray-700">
          Practice for your draft with fast mocks against realistic opponents. Test strategies, draft from any position,
          and get grades instantly. <span className="text-blue-600 cursor-pointer">read more</span>
        </p>
      </div>
    </Card>
  )
}
