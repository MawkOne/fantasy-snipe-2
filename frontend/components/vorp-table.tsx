"use client"

import { useEffect, useMemo, useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

type VorpItem = {
  player_id: number
  name: string
  team: string
  position: string
  gp: number
  points: number
  vorp_pts: number
  tier?: number
  group?: "C" | "W" | "D"
}

export default function VorpTable() {
  const [forwards, setForwards] = useState<VorpItem[]>([])
  const [defence, setDefence] = useState<VorpItem[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchVorp = async () => {
      try {
        setLoading(true)
        const url = `/api/vorp?season=20242025&centers_keep=40&wings_keep=60&defence_keep=40&tiers=15&method=quantile&value=production&min_gp=11`
        const res = await fetch(url, { cache: "no-store" })
        if (!res.ok) throw new Error(`Failed to load VORP (${res.status})`)
        const data = await res.json()
        const c: VorpItem[] = (data?.centers || []).map((x: any) => ({ ...x, group: "C" }))
        const w: VorpItem[] = (data?.wings || []).map((x: any) => ({ ...x, group: "W" }))
        const d: VorpItem[] = (data?.defence || []).map((x: any) => ({ ...x, group: "D" }))
        setForwards([...c, ...w])
        setDefence(d)
      } catch (e: any) {
        setError(e?.message || "Failed to load VORP")
      } finally {
        setLoading(false)
      }
    }
    fetchVorp()
  }, [])

  const grouped = useMemo(() => {
    const rows = [...forwards, ...defence]
    const sorted = rows
      .slice()
      .sort((a, b) => (a.tier ?? 99) - (b.tier ?? 99) || (b.vorp_pts ?? 0) - (a.vorp_pts ?? 0))
      .map((r, idx) => ({ rank: idx + 1, ...r }))
    const groups: Record<number, VorpItem[]> = {}
    for (const r of sorted) {
      const t = (r.tier ?? 99) as number
      if (!groups[t]) groups[t] = []
      groups[t].push(r)
    }
    const orderedTiers = Object.keys(groups)
      .map((k) => Number(k))
      .sort((a, b) => a - b)
    return { groups, orderedTiers }
  }, [forwards, defence])

  const tierBg = (tier?: number) => {
    if (!tier) return "bg-gray-100"
    if (tier === 1) return "bg-yellow-100"
    if (tier <= 3) return "bg-blue-100"
    if (tier <= 6) return "bg-green-100"
    return "bg-gray-100"
  }

  return (
    <div className="bg-white rounded-lg border overflow-hidden">
      <Table className="text-sm">
        <TableHeader>
          <TableRow>
            <TableHead className="w-12 py-1">RK</TableHead>
            <TableHead className="py-1">PLAYER</TableHead>
            <TableHead className="w-16 py-1">POS</TableHead>
            <TableHead className="w-16 py-1">TEAM</TableHead>
            <TableHead className="w-14 py-1">GRP</TableHead>
            <TableHead className="w-16 py-1">TIER</TableHead>
            <TableHead className="w-16 py-1">GP</TableHead>
            <TableHead className="w-16 py-1">PTS</TableHead>
            <TableHead className="w-20 py-1">VORP(PTS)</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {loading && (
            <TableRow>
              <TableCell colSpan={9}>Loading...</TableCell>
            </TableRow>
          )}
          {error && !loading && (
            <TableRow>
              <TableCell colSpan={9} className="text-red-600">{error}</TableCell>
            </TableRow>
          )}
          {!loading && !error && grouped.orderedTiers.map((t) => (
            <>
              <TableRow key={`tier-${t}`} className="bg-blue-600 text-white h-8">
                <TableCell colSpan={9} className="font-semibold text-center py-1">
                  {`Tier ${t}`} <span className="ml-2 text-xs">(VORP/PT gaps)</span>
                </TableCell>
              </TableRow>
              {grouped.groups[t].map((p) => (
                <TableRow key={`${t}-${p.group}-${p.player_id}`} className={`${tierBg(p.tier)} h-9`}>
                  <TableCell className="font-medium py-1">{p.rank}</TableCell>
                  <TableCell className="py-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium">{p.name}</span>
                    </div>
                  </TableCell>
                  <TableCell className="py-1">
                    <Badge variant="outline">{p.position || "-"}</Badge>
                  </TableCell>
                  <TableCell className="py-1">{p.team}</TableCell>
                  <TableCell className="py-1">{p.group}</TableCell>
                  <TableCell className="py-1">{p.tier ?? "-"}</TableCell>
                  <TableCell className="py-1">{p.gp}</TableCell>
                  <TableCell className="py-1">{p.points}</TableCell>
                  <TableCell className="py-1">{p.vorp_pts}</TableCell>
                </TableRow>
              ))}
            </>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}


