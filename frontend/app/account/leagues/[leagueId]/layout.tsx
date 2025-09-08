import type { ReactNode } from "react"
import { LeagueHeader } from "@/components/league-header"

export default function LeagueLayout({
  params,
  children,
}: {
  params: { leagueId: string }
  children: ReactNode
}) {
  // Mock league data; in the future fetch from DB by params.leagueId
  const league = {
    id: params.leagueId,
    name: params.leagueId === "lg_1" ? "Cross Border League of Donuts (CBS)" : "Friends & Family Hockey",
    teamName: params.leagueId === "lg_1" ? "TacoCorp" : "Ice Wizards",
    provider: (params.leagueId === "lg_1" ? "CBS" : "Yahoo") as "CBS" | "Yahoo",
    logoUrl: params.leagueId === "lg_1" ? "/taco-corp-league-logo-green-cactus.png" : "/blue-hockey-wizard-logo.png",
  }

  const baseHref = `/account/leagues/${params.leagueId}`

  return (
    <div className="rounded-xl">
      <LeagueHeader
        leagueId={league.id}
        name={league.name}
        teamName={league.teamName}
        provider={league.provider}
        logoUrl={league.logoUrl}
        baseHref={baseHref}
      />
      <div className="p-4 md:p-6">{children}</div>
    </div>
  )
}
