import React from "react"

type LeagueTeam = {
  team_id: string
  team_name: string
  abbrev?: string | null
  long_abbr?: string | null
  short_name?: string | null
  owner_id?: string | null
  logo_url?: string | null
  is_active?: boolean | null
  total_salary?: number | string | null
  total_players?: number | null
}

async function fetchTeams(leagueId: string | number): Promise<LeagueTeam[]> {
  const apiBase = (process.env.NEXT_PUBLIC_API_BASE && process.env.NEXT_PUBLIC_API_BASE.startsWith('http'))
    ? process.env.NEXT_PUBLIC_API_BASE
    : 'http://localhost:8000'
  const url = `${apiBase}/api/public/cbs/league/uhhp/teams`
  const res = await fetch(url, { cache: "no-store" })
  if (!res.ok) return []
  const data = await res.json()
  return Array.isArray(data?.teams) ? data.teams as LeagueTeam[] : []
}

export default async function LeagueTeams({ leagueId }: { leagueId: string | number }) {
  const teams = await fetchTeams(leagueId)
  if (!teams.length) {
    return (
      <div className="rounded-md border p-4 text-sm text-gray-600">No teams found for league {String(leagueId)}.</div>
    )
  }
  return (
    <div className="rounded-md border">
      <div className="px-4 py-3 border-b font-medium">League Teams</div>
      <ul className="divide-y">
        {teams.map((t) => (
          <li key={t.team_id} className="px-4 py-3 flex items-center gap-3">
            {t.logo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={t.logo_url} alt={t.team_name} className="h-8 w-8 rounded object-cover" />
            ) : (
              <div className="h-8 w-8 rounded bg-gray-200" />
            )}
            <div className="flex-1">
              <div className="font-medium">{t.team_name}</div>
              <div className="text-xs text-gray-500">Owner: {t.owner_id || "Unknown"}</div>
            </div>
            <div className="text-xs text-gray-500">
              {typeof t.total_players === 'number' ? `${t.total_players} players` : null}
              {typeof t.total_salary !== 'undefined' ? ` | $${Number(t.total_salary || 0).toLocaleString()}` : null}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}


