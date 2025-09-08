"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { ChevronLeft, MoreHorizontal } from "lucide-react"

export type LeagueHeaderProps = {
  leagueId: string
  name: string
  teamName: string
  provider: "Yahoo" | "ESPN" | "CBS" | "Sleeper" | "Fantrax"
  logoUrl?: string
  baseHref: string
}

export function LeagueHeader(props: LeagueHeaderProps) {
  const { leagueId, name, teamName, provider, logoUrl, baseHref } = props
  return (
    <div className="relative">
      <div className="h-28 w-full rounded-t-xl bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900 via-blue-800 to-blue-700" />
      <div className="absolute inset-x-0 top-1/2 translate-y-[-40%] px-4 md:px-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/account/leagues"
              className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-white shadow ring-1 ring-gray-200"
              aria-label="Back to My Leagues"
            >
              <ChevronLeft className="h-5 w-5" />
            </Link>
            <div className="h-12 w-12 rounded-full overflow-hidden ring-2 ring-white bg-gray-100">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={logoUrl ?? "/placeholder.svg?height=48&width=48&query=league%20logo"}
                alt="League logo"
                className="h-full w-full object-cover"
              />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl md:text-2xl font-semibold text-white drop-shadow">{name}</h1>
                <span className="text-xs md:text-sm rounded bg-white/90 px-2 py-0.5 font-medium text-gray-800">
                  {teamName} – {provider}
                </span>
              </div>
              <div className="mt-1">
                <Link href="/account/leagues" className="text-xs text-white/90 hover:underline">
                  My Leagues
                </Link>
                <span className="text-xs text-white/70"> {" / "} </span>
                <span className="text-xs text-white/90">{name}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link href="/sync">
              <Button variant="outline" className="bg-white text-blue-700 hover:bg-blue-50">
                Resync League
              </Button>
            </Link>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="text-white hover:bg-white/10" aria-label="More actions">
                  <MoreHorizontal className="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-44">
                <DropdownMenuItem onClick={() => alert(`Share ${leagueId}`)}>Share League</DropdownMenuItem>
                <DropdownMenuItem onClick={() => alert(`Remove ${leagueId}`)} className="text-red-600">
                  Disconnect
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {/* Tabs nav */}
      <div className="mt-14 border-t border-gray-200" />
      <LeagueTabs baseHref={baseHref} />
    </div>
  )
}

import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

function LeagueTabs({ baseHref }: { baseHref: string }) {
  const pathname = usePathname()
  const tabs = [
    { href: `${baseHref}/overview`, label: "Overview" },
    { href: `${baseHref}/draft-picks`, label: "Draft Picks" },
    { href: `${baseHref}/keepers`, label: "Keepers" },
    { href: `${baseHref}/mock-drafts`, label: "Mock Drafts" },
    { href: `${baseHref}/options`, label: "Options" },
  ]
  return (
    <div className="px-4 md:px-6">
      <div className="flex items-center gap-4 overflow-x-auto">
        {tabs.map((t) => {
          const active = pathname.startsWith(t.href)
          return (
            <Link
              key={t.href}
              href={t.href}
              className={cn(
                "py-3 border-b-2 -mb-px text-sm font-medium transition-colors whitespace-nowrap",
                active ? "border-blue-600 text-blue-700" : "border-transparent text-gray-600 hover:text-gray-900",
              )}
            >
              {t.label}
            </Link>
          )
        })}
      </div>
    </div>
  )
}
