"use client"

import { useEffect, useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

type RankingRow = {
  rank: number
  player_id: number
  name: string
  team: string
  position: string
  gp: number
  goals: number
  assists: number
  points: number
  archetype?: string
}

export default function RankingsTable() {
  const [rows, setRows] = useState<RankingRow[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchRankings = async () => {
      try {
        setLoading(true)
        const res = await fetch(`/api/rankings?season=20242025`, { cache: "no-store" })
        if (!res.ok) throw new Error(`Failed to load rankings (${res.status})`)
        const data = await res.json()
        setRows(data?.results || [])
      } catch (e: any) {
        setError(e?.message || "Failed to load rankings")
      } finally {
        setLoading(false)
      }
    }
    fetchRankings()
  }, [])

  return (
    <div className="bg-white rounded-lg border overflow-hidden">
      <Table className="text-sm">
        <TableHeader>
          <TableRow>
            <TableHead className="w-12 py-1">RK</TableHead>
            <TableHead className="py-1">PLAYER</TableHead>
            <TableHead className="w-16 py-1">POS</TableHead>
            <TableHead className="w-16 py-1">TEAM</TableHead>
            <TableHead className="w-28 py-1">ARCHETYPE</TableHead>
            <TableHead className="w-16 py-1">GP</TableHead>
            <TableHead className="w-16 py-1">G</TableHead>
            <TableHead className="w-16 py-1">A</TableHead>
            <TableHead className="w-16 py-1">P</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {loading && (
            <TableRow>
              <TableCell colSpan={8}>Loading...</TableCell>
            </TableRow>
          )}
          {error && !loading && (
            <TableRow>
              <TableCell colSpan={8} className="text-red-600">{error}</TableCell>
            </TableRow>
          )}
          {!loading && !error && rows.map((p) => (
            <TableRow key={p.player_id} className="h-9">
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
              <TableCell className="py-1">{p.archetype || '-'}</TableCell>
              <TableCell className="py-1">{p.gp}</TableCell>
              <TableCell className="py-1">{p.goals}</TableCell>
              <TableCell className="py-1">{p.assists}</TableCell>
              <TableCell className="py-1">{p.points}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
