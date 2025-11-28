"use client"

import { Button } from "@/components/ui/button"
import LeagueRow, { type League } from "@/components/league-row"
import Link from "next/link"

const leagues: League[] = [
  {
    id: "lg_1",
    name: "Cross Border League of Donuts",
    teamName: "TacoCorp",
    provider: "CBS",
    sport: "NHL",
    draftDateTz: "Aug 28, 10:00 PM EDT",
    formatTags: ["CUSTOM", "Keepers"],
    teamsCount: 12,
    logoUrl: "/taco-corp-league-logo-green-cactus.png",
  },
  {
    id: "lg_2",
    name: "Friends & Family Hockey",
    teamName: "Ice Wizards",
    provider: "Yahoo",
    sport: "NHL",
    draftDateTz: "Sep 3, 7:30 PM EDT",
    formatTags: ["Points"],
    teamsCount: 10,
    logoUrl: "/blue-hockey-wizard-logo.png",
  },
]

export default function AccountLeaguesPage() {
  return (
    <div className="p-4 md:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold">Leagues</h1>
          <p className="text-gray-600 mt-1">View all of your leagues synced with FantasySnipe.ai</p>
        </div>
        <Link href="/sync">
          <Button className="bg-blue-600 hover:bg-blue-700">Sync a league</Button>
        </Link>
      </div>

      <div className="mt-6 space-y-3">
        {leagues.map((lg) => (
          <LeagueRow key={lg.id} league={lg} />
        ))}
      </div>
    </div>
  )
}
