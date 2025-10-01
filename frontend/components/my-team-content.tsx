"use client"

import { useEffect, useMemo, useState } from "react"

type RosterRow = {
  position: string
  player_name: string
  nhl_player_id?: number
  status?: string | null
  salary?: number | string | null
  years?: number | null
  fantasy_points?: number | null
}

export default function MyTeamContent() {
  const [rows, setRows] = useState<RosterRow[] | null>(null)
  const [teamName] = useState<string>("New Oilers Nation")
  const [loading, setLoading] = useState<boolean>(false)
  const [rosterPositions, setRosterPositions] = useState<Record<string, number>>({})

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith("http"))
          ? (process.env.NEXT_PUBLIC_API_BASE as string)
          : "http://localhost:8000"
        // Fetch league state to get roster position rules
        try {
          const st = await fetch(`${apiBase}/api/public/cbs/league/uhhp/state`, { cache: "no-store" })
          if (st.ok) {
            const stateJson = await st.json()
            const rp = (stateJson?.rules?.roster_positions) || (stateJson?.roster_positions) || null
            if (rp) {
              if (typeof rp === 'string') {
                try { setRosterPositions(JSON.parse(rp)) } catch { /* ignore */ }
              } else if (typeof rp === 'object') {
                setRosterPositions(rp as Record<string, number>)
              }
            }
          }
        } catch {}
        const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/draft_state`, { cache: "no-store" })
        if (!res.ok) { setRows([]); return }
        const data = await res.json()
        const teams = Array.isArray(data?.teams) ? data.teams as any[] : []
        const rosters = Array.isArray(data?.rosters) ? data.rosters as any[] : []
        const team = teams.find((t: any) => (t?.team_name || "").toString() === teamName)
        const tid = team?.team_id
        const mine = rosters.filter((r: any) => String(r.team_id) === String(tid))
        const mapped: RosterRow[] = mine.map((r: any) => ({
          position: (r.position || '').toString().toUpperCase(),
          player_name: r.player_name || String(r.cbs_player_id || r.nhl_player_id || ''),
          nhl_player_id: typeof r.nhl_player_id === 'number' ? r.nhl_player_id : undefined,
          status: r.status || null,
          salary: r.salary ?? null,
          years: r.years ?? null,
          fantasy_points: typeof r.fantasy_points === 'number' ? r.fantasy_points : null,
        }))
        setRows(mapped)
      } catch {
        setRows([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [teamName])

  const sortedRows = useMemo(() => {
    const base = rows || []
    if (!base.length) return base
    // Position order based on roster rules (fallback order)
    const orderList = ['C','W','F','D','G']
    const activePositions = orderList.filter((p) => rosterPositions && Object.prototype.hasOwnProperty.call(rosterPositions, p))
    const finalOrder = activePositions.length ? activePositions : orderList
    const pri: Record<string, number> = {}
    finalOrder.forEach((p, i) => { pri[p] = i })
    return [...base].sort((a, b) => {
      const pa = pri[(a.position || '').toUpperCase()] ?? 999
      const pb = pri[(b.position || '').toUpperCase()] ?? 999
      if (pa !== pb) return pa - pb
      // Secondary: salary desc (numbers first)
      const sa = typeof a.salary === 'number' ? a.salary : -1
      const sb = typeof b.salary === 'number' ? b.salary : -1
      return sb - sa
    })
  }, [rows, rosterPositions])

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">My Team</h1>
        <p className="text-gray-600">{teamName}</p>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">POS</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PLAYER</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">STATUS</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">SALARY</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">YEARS</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">NHL ID</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">FP</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading && (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={`s-${i}`} className="hover:bg-gray-50">
                    <td className="px-4 py-4"><div className="h-3 w-6 bg-gray-200 rounded" /></td>
                    <td className="px-4 py-4"><div className="h-3 w-40 bg-gray-200 rounded" /></td>
                    <td className="px-4 py-4"><div className="h-3 w-10 bg-gray-200 rounded" /></td>
                    <td className="px-4 py-4 text-right"><div className="h-3 w-12 bg-gray-200 rounded inline-block" /></td>
                    <td className="px-4 py-4 text-right"><div className="h-3 w-8 bg-gray-200 rounded inline-block" /></td>
                    <td className="px-4 py-4 text-right"><div className="h-3 w-16 bg-gray-200 rounded inline-block" /></td>
                    <td className="px-4 py-4 text-right"><div className="h-3 w-8 bg-gray-200 rounded inline-block" /></td>
                  </tr>
                ))
              )}
              {!loading && (sortedRows || []).map((r, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-4">
                    <span className="text-sm font-medium text-gray-900">{r.position}</span>
                  </td>
                  <td className="px-4 py-4">
                    <div className="text-sm font-medium text-blue-600">{r.player_name}</div>
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-900">{r.status || '—'}</td>
                  <td className="px-4 py-4 text-sm text-gray-900 text-right">{typeof r.salary === 'number' ? `$${r.salary.toLocaleString()}` : (r.salary ? `$${r.salary}` : '—')}</td>
                  <td className="px-4 py-4 text-sm text-gray-900 text-right">{r.years ?? '—'}</td>
                  <td className="px-4 py-4 text-sm text-gray-900 text-right">{r.nhl_player_id ?? '—'}</td>
                  <td className="px-4 py-4 text-sm text-gray-900 text-right">{typeof r.fantasy_points === 'number' ? r.fantasy_points.toFixed(1) : '—'}</td>
                </tr>
              ))}
              {!loading && (rows || []).length === 0 && (
                <tr>
                  <td className="px-4 py-6 text-sm text-gray-500" colSpan={7}>No players found for {teamName}.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
