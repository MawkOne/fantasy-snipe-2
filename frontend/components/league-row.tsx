"use client"

import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"
import { MoreHorizontal } from "lucide-react"
import SettingsDialog from "./settings-dialog"

export type League = {
  id: string
  name: string
  teamName: string
  provider: "CBS" | "Yahoo" | "ESPN" | "Sleeper" | "Fantrax"
  sport: "NHL"
  draftDateTz: string
  formatTags: string[]
  teamsCount: number
  logoUrl: string
}

export default function LeagueRow({ league }: { league: League }) {
  return (
    <div className="rounded-lg border hover:shadow-sm transition bg-white">
      <div className="p-4 flex items-center gap-4">
        <div className="relative h-10 w-10 rounded-md overflow-hidden border">
          <Image
            src={league.logoUrl || "/placeholder.svg?height=40&width=40&query=league%20logo"}
            alt={`${league.name} logo`}
            fill
            sizes="40px"
            className="object-cover"
            priority={false}
          />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <div className="font-medium truncate">{league.name}</div>
            <span className="text-sm text-gray-500">
              • {league.teamName} – {league.provider}
            </span>
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <span className="text-xs text-gray-500">Draft Date: {league.draftDateTz}</span>
            <span className="text-gray-300">•</span>
            <span className="text-xs text-gray-500">{league.teamsCount} Team</span>
            <div className="flex flex-wrap gap-1">
              {league.formatTags.map((t) => (
                <Badge key={t} variant="secondary" className="text-[10px]">
                  {t}
                </Badge>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <SettingsDialog league={league} trigger={<Button className="bg-blue-600 hover:bg-blue-700">Open</Button>} />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="text-gray-600">
                <MoreHorizontal className="h-5 w-5" />
                <span className="sr-only">More</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>Rename</DropdownMenuItem>
              <DropdownMenuItem>Re-sync</DropdownMenuItem>
              <DropdownMenuItem className="text-red-600">Remove</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  )
}
