"use client"

import { useMemo, useState, useEffect } from "react"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Dialog, DialogContent, DialogClose } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Clock, Search, Settings, Stars, Star, X, Ellipsis, Pause, Play } from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

type Player = {
  id: string
  name: string
  team: string
  pos: string
  bye: number
  overall: number
  adp: number
  expertPct: number
  headshot?: string
}

type Pick = {
  overall: number
  round: number
  pickInRound: number
  teamId: string
  player?: Player
}

type Team = {
  id: string
  name: string
  needs?: string[]
}

const samplePlayers: Player[] = [
  {
    id: "mcdavid",
    name: "Connor McDavid",
    team: "EDM",
    pos: "C",
    bye: 14,
    overall: 1,
    adp: 1,
    expertPct: 92,
    headshot: "/connor-mcdavid-headshot-hockey.png",
  },
  {
    id: "matthews",
    name: "Auston Matthews",
    team: "TOR",
    pos: "C",
    bye: 8,
    overall: 2,
    adp: 2,
    expertPct: 84,
    headshot: "/auston-matthews-headshot-hockey.png",
  },
  {
    id: "kucherov",
    name: "Nikita Kucherov",
    team: "TBL",
    pos: "RW",
    bye: 9,
    overall: 3,
    adp: 3,
    expertPct: 75,
    headshot: "/nikita-kucherov-headshot-hockey.png",
  },
  {
    id: "rantanen",
    name: "Mikko Rantanen",
    team: "COL",
    pos: "RW",
    bye: 10,
    overall: 4,
    adp: 4,
    expertPct: 61,
    headshot: "/mikko-rantanen-headshot-hockey.png",
  },
  {
    id: "mackinnon",
    name: "Nathan MacKinnon",
    team: "COL",
    pos: "C",
    bye: 10,
    overall: 5,
    adp: 5,
    expertPct: 58,
    headshot: "/nathan-mackinnon-headshot-hockey.png",
  },
  {
    id: "pastrnak",
    name: "David Pastrnak",
    team: "BOS",
    pos: "RW",
    bye: 6,
    overall: 6,
    adp: 6,
    expertPct: 49,
    headshot: "/david-pastrnak-headshot-hockey.png",
  },
]

function posPillClass(pos: string) {
  switch (pos.toUpperCase()) {
    case "C":
      return "bg-sky-100 text-sky-800"
    case "LW":
      return "bg-emerald-100 text-emerald-800"
    case "RW":
      return "bg-violet-100 text-violet-800"
    case "D":
      return "bg-slate-100 text-slate-800"
    case "G":
      return "bg-amber-100 text-amber-800"
    default:
      return "bg-slate-100 text-slate-700"
  }
}

function teamAbbr(name: string | undefined | null): string {
  const s = (name || "").toString()
  const parts = s.split(/\s+/).filter(Boolean)
  const letters = parts
    .map((w) => (w.match(/[A-Za-z]/)?.[0] || "").toUpperCase())
    .join("")
    .slice(0, 3)
  if (letters.length >= 2) return letters
  const fallback = s.replace(/[^A-Za-z]/g, "").toUpperCase().slice(0, 3)
  return fallback || "TAK"
}

function normalizeName(name: string | undefined | null): string {
  return (name || "").toString().trim().toLowerCase()
}

function abbreviatePlayerName(fullName: string | undefined | null): string {
  const raw = (fullName || "").toString().replace(/\*/g, "").trim()
  if (!raw) return ""
  const parts = raw.split(/\s+/).filter(Boolean)
  if (parts.length === 1) return parts[0]
  const first = parts[0]
  const last = parts.slice(1).join(" ")
  const initial = first ? `${first[0].toUpperCase()}.` : ""
  return `${initial} ${last}`.trim()
}

export default function DraftRoom({ autoLoadUhhp = false }: { autoLoadUhhp?: boolean }) {
  // Teams (snake draft with 12 teams; you are team[9] e.g., pick 1.10)
  const teams: Team[] = useMemo(
    () => [
      { id: "t1", name: "Pure Chaos", needs: ["C", "RW", "D"] },
      { id: "t2", name: "South Calgary Cowboys", needs: ["LW", "D", "G"] },
      { id: "t3", name: "Rodgers Belt", needs: ["C", "LW", "D"] },
      { id: "t4", name: "Deep Ballz", needs: ["RW", "G", "D"] },
      { id: "you", name: "TacoCorp", needs: ["C", "RW"] },
      { id: "t6", name: "Harbaugh You Blow Me", needs: ["C", "RB", "WR", "TE"] },
      { id: "t7", name: "Far East Invasion", needs: ["C", "RW", "D", "G"] },
      { id: "t8", name: "Nordic Knights", needs: ["LW", "D"] },
      { id: "t9", name: "Frozen Fury", needs: ["G", "D"] },
      { id: "t10", name: "Icy Hot", needs: ["C", "LW"] },
      { id: "t11", name: "Puck Wizards", needs: ["RW", "G"] },
      { id: "t12", name: "Blue Line Bandits", needs: ["D", "C"] },
    ],
    [],
  )

  // Build round 1 order with some picks already made (1.06 - 1.09)
  const [picks, setPicks] = useState<Pick[]>(
    Array.from({ length: 12 }, (_, i) => ({
      overall: i + 1,
      round: 1,
      pickInRound: i + 1,
      teamId: teams[i]?.id ?? "t?",
      player:
        i < 5
          ? samplePlayers[i]
          : i === 5
            ? samplePlayers[0]
            : i === 6
              ? samplePlayers[1]
              : i === 7
                ? samplePlayers[2]
                : i === 8
                  ? samplePlayers[3]
                  : undefined,
    })),
  )

  // current pick index (0-based). You are 1.10 (index 9)
  const [currentIdx, setCurrentIdx] = useState(9)
  const currentPick = picks[currentIdx]
  const yourTeamId = "you"
  const isYouOnClock = currentPick?.teamId === yourTeamId

  // Timer state (30s countdown with pause)
  const [timeLeft, setTimeLeft] = useState<number>(30)
  const [timerRunning, setTimerRunning] = useState<boolean>(true)
  const [phase, setPhase] = useState<"Choosing Nomination" | "Submit Bid" | "Tiebreak">("Choosing Nomination")
  useEffect(() => {
    if (!timerRunning) return
    const id = setInterval(() => {
      setTimeLeft((t) => (t > 0 ? t - 1 : 0))
    }, 1000)
    return () => clearInterval(id)
  }, [timerRunning])
  function toggleTimer() {
    setTimerRunning((r) => !r)
  }
  function formatTime(s: number) {
    const mm = Math.floor(s / 60)
    const ss = s % 60
    return `${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`
  }

  // Bid aggregation state (must be declared before reveal logic)
  const [gmBids, setGmBids] = useState<Record<string, number>>({})
  const [revealTimer, setRevealTimer] = useState<number | null>(null)
  const [revealed, setRevealed] = useState<boolean>(false)
  const [auctionOrder, setAuctionOrder] = useState<string[]>([])
  const [tieAudit, setTieAudit] = useState<Array<{ pick: number; winners: string[]; advantage: string | null }>>([])

  // 3s reveal countdown when all bids submitted
  const allSubmitted = useMemo(() => teams.every((t) => gmBids[t.id] !== undefined), [teams, gmBids])
  useEffect(() => {
    if (revealed) return
    if (allSubmitted && revealTimer === null) setRevealTimer(3)
  }, [allSubmitted, revealTimer, revealed])
  useEffect(() => {
    if (revealTimer === null) return
    if (revealTimer <= 0) {
      setRevealTimer(null)
      setRevealed(true)
      // Auto-assign the won player into the winner's roster active slots
      try {
        const top = (() => {
          const vals = Object.values(gmBids)
          if (!vals.length) return null as number | null
          return Math.max(...vals)
        })()
        if (top != null && nominated) {
          const winners = teams.filter((t) => gmBids[t.id] === top)
          let finalWinnerId: string | null = winners[0]?.id || null
          if (winners.length > 1 && (auctionOrder || []).length) {
            const tiedNames = winners.map((t) => t.name)
            // Decide by whoever is higher in current order
            let bestIdx = Infinity
            let advName: string | null = null
            for (const t of winners) {
              const nm = t.name
              const idx = auctionOrder.findIndex((n) => n === nm)
              if (idx >= 0 && idx < bestIdx) { bestIdx = idx; advName = nm }
            }
            if (advName) {
              finalWinnerId = (teams.find((t) => t.name === advName)?.id) || finalWinnerId
              // Move the winner to the bottom of the order
              setAuctionOrder((prev) => {
                const i = prev.findIndex((n) => n === advName)
                if (i < 0) return prev
                const copy = [...prev]
                const [moved] = copy.splice(i, 1)
                copy.push(moved)
                return copy
              })
              // Audit log entry
              setTieAudit((prev) => ([...prev, { pick: (uhhpPicks?.length || 0) + 1, winners: tiedNames, advantage: advName }]))
            }
          }
          if (finalWinnerId) {
            const newPick = { team: teamAbbr(teams.find((t) => t.id === finalWinnerId)?.name || ""), player: nominated.player, pos: (nominated.pos || "").toString().toUpperCase(), price: top }
            setUhhpPicks((prev) => ([...(prev || []), newPick]))
          }
        }
      } catch (e) {}
      return
    }
    const id = setTimeout(() => setRevealTimer((v) => (v ?? 0) - 1), 1000)
    return () => clearTimeout(id)
  }, [revealTimer])

  const topBid = useMemo(() => {
    if (!revealed) return null as number | null
    const vals = Object.values(gmBids)
    if (!vals.length) return null
    return Math.max(...vals)
  }, [gmBids, revealed])
  const tieTeams = useMemo(() => {
    if (!revealed || topBid == null) return [] as string[]
    return teams.filter((t) => gmBids[t.id] === topBid).map((t) => t.id)
  }, [revealed, topBid, teams, gmBids])
  const tieAdvantageTeamId = useMemo(() => {
    if (tieTeams.length <= 1) return null as string | null
    if (auctionOrder && auctionOrder.length) {
      let best: string | null = null
      let bestIdx = Infinity
      for (const id of tieTeams) {
        const team = teams.find((t) => t.id === id)
        const name = team?.name ?? ""
        const idx = auctionOrder.findIndex((n) => n === name)
        if (idx >= 0 && idx < bestIdx) {
          bestIdx = idx
          best = id
        }
      }
      if (best) return best
    }
    return tieTeams[0] ?? null
  }, [tieTeams, auctionOrder, teams])

  // Suggestions + rankings
  const [suggestions] = useState<Player[]>([samplePlayers[0], samplePlayers[1], samplePlayers[5], samplePlayers[3]])
  const [rankings] = useState<Player[]>(
    Array.from({ length: 24 }, (_, i) => {
      const base = samplePlayers[i % samplePlayers.length]
      return {
        ...base,
        id: `${base.id}-${i}`,
        overall: i + 1,
        adp: i + 1,
        expertPct: 99 - (i % 8) * 4,
      }
    }),
  )

  // Left rail tabs state
  const [leftTab, setLeftTab] = useState<"rankings" | "teams" | "queue">("rankings")
  const [modalOpen, setModalOpen] = useState(false)
  const [modalPlayer, setModalPlayer] = useState<Player | null>(null)
  const [showAvailable, setShowAvailable] = useState(false)
  const [posFilter, setPosFilter] = useState<"All" | "C" | "W" | "D" | "G">("All")
  const [faFilter, setFaFilter] = useState<"All" | "UFA" | "RFA">("All")
  const [bidAmount, setBidAmount] = useState<string>("2")
  const [nominated, setNominated] = useState<any | null>(null)
  const [bidSubmitted, setBidSubmitted] = useState<Record<string, boolean>>({})
  const [submittedHover, setSubmittedHover] = useState<boolean>(false)
  const [currentPickNum, setCurrentPickNum] = useState<number>(6)
  const [uhhpPicks, setUhhpPicks] = useState<any[] | null>(null)
  const [fpMap, setFpMap] = useState<Record<string, number>>({})
  const [ageMap, setAgeMap] = useState<Record<string, number>>({})
  const [projections, setProjections] = useState<any[] | null>(null)
  const [projectionSource, setProjectionSource] = useState<"avg_experts" | "clusters">("avg_experts")
  const [stage1Teams, setStage1Teams] = useState<any[] | null>(null)
  const [selectedTeamName, setSelectedTeamName] = useState<string | null>(null)
  const [benchSet, setBenchSet] = useState<Set<string>>(new Set())
  const [targets, setTargets] = useState<Record<string, { player: any | null; bid: string }>>({})

  function toggleBench(playerName: string) {
    const key = normalizeName(playerName)
    setBenchSet((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }
  async function loadUhhp() {
    try {
      const url = projectionSource === "avg_experts" ? "/api/uhhp/state?mock=1" : "/api/uhhp/state"
      const res = await fetch(url, { cache: "no-store" })
      const data = await res.json()
      setUhhpPicks((data?.auction?.results as any[]) || [])
      setAuctionOrder((data?.auction?.order as string[]) || [])
      setFpMap((data?.fpMap as Record<string, number>) || {})
      setAgeMap((data?.ageMap as Record<string, number>) || {})
      setProjections((data?.projections as any[]) || null)
      setStage1Teams((data?.stage1Teams as any[]) || null)
      if (Array.isArray(data?.stage1Teams) && data.stage1Teams.length > 0) {
        const prefer = (data.stage1Teams as any[]).find((t: any) => (t?.team_name || "") === "New Oilers Nation")
        const pickName = (prefer?.team_name as string) || (data.stage1Teams[0]?.team_name as string) || "New Oilers Nation"
        setSelectedTeamName(String(pickName))
      } else if (!selectedTeamName) {
        setSelectedTeamName("New Oilers Nation")
      }
      toast.success("Loaded UHHP draft state")
    } catch (e) {
      toast.error("Failed to load UHHP state")
    }
  }

  const uhhpTop50 = useMemo(() => (uhhpPicks ? uhhpPicks.slice(0, 50) : null), [uhhpPicks])
  const uhhpFilled50 = useMemo(() => {
    if (!uhhpPicks) return null
    const list: Array<{ kind: "taken" | "pending" | "nominated"; data?: any; team?: string }> = []
    const total = 50
    const takenCount = Math.min(uhhpPicks.length, total)
    for (let i = 0; i < takenCount; i++) list.push({ kind: "taken", data: uhhpPicks[i] })
    for (let i = takenCount; i < total; i++) {
      const nomTeam = auctionOrder.length ? auctionOrder[i % auctionOrder.length] : "Nomination"
      if (i === takenCount && nominated) {
        list.push({ kind: "nominated", data: nominated, team: nomTeam })
      } else {
        list.push({ kind: "pending", team: nomTeam })
      }
    }
    return list
  }, [uhhpPicks, auctionOrder, nominated])

  function openPlayer(p: Player) {
    setModalPlayer(p)
    setModalOpen(true)
  }

  function draftPlayer(p: Player) {
    if (!isYouOnClock) return
    setPicks((prev) => {
      const copy = [...prev]
      copy[currentIdx] = { ...copy[currentIdx], player: p }
      return copy
    })
    // advance to next pick (1.11)
    setCurrentIdx((i) => Math.min(i + 1, picks.length - 1))
  }

  useEffect(() => {
    if (autoLoadUhhp) {
      loadUhhp()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoLoadUhhp, projectionSource])

  return (
    <div className="min-h-screen bg-white grid grid-rows-[56px_1fr]">
      {/* Draft top bar */}
      <div className="bg-slate-900 text-white">
        <div className="max-w-screen-2xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded bg-emerald-500 flex items-center justify-center text-xs font-bold">
                TS
              </div>
              <div className="font-semibold">Draft Simulator</div>
            </div>
            <button className="ml-3 inline-flex items-center gap-2 rounded bg-slate-800 px-3 py-1.5 text-sm hover:bg-slate-700">
              <Stars className="w-4 h-4" />
              Auto Draft
            </button>
            <button className="p-2 hover:bg-slate-800 rounded">
              <Settings className="w-4 h-4" />
            </button>
            <button onClick={loadUhhp} className="p-2 hover:bg-slate-800 rounded">
              <Clock className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 max-w-xl mx-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search players"
                className="pl-9 bg-slate-800 border-slate-700 text-white placeholder:text-slate-400"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={toggleTimer}
              className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded bg-slate-800 hover:bg-slate-700"
              aria-label={timerRunning ? "Pause" : "Resume"}
            >
              {timerRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              <span>{timerRunning ? "Pause" : "Resume"}</span>
            </button>
            <div className="hidden md:flex items-center gap-2 text-sm">
              <span className="font-semibold">{phase}</span>
            </div>
            <div className="text-sm font-semibold tabular-nums">{formatTime(timeLeft)}</div>
          </div>
        </div>
      </div>

      {/* Main content columns */}
      <div className="w-full grid grid-cols-1 md:grid-cols-[280px_minmax(0,1fr)_340px] gap-4 px-0 py-4 h-full items-stretch">
        {/* Left: Rankings rail with tabs */}
        <aside className="rounded-none border-r bg-white h-full flex flex-col min-h-0">
          {/* Tabs header (Rankings | Teams | Queue) */}
          <div className="px-3 pt-2">
            <div className="flex items-center gap-2">
              {(["rankings", "queue"] as const).map((t) => {
                const labels: Record<typeof t, string> = {
                  rankings: "Auction",
                  queue: "Tie Break",
                } as const
                const active = leftTab === t
                return (
                  <button
                    key={t}
                    onClick={() => setLeftTab(t)}
                    className={cn(
                      "relative px-3 py-1.5 rounded-full text-sm transition-colors",
                      active ? "text-blue-700 ring-1 ring-blue-300 bg-blue-50" : "text-slate-700 hover:bg-slate-50",
                    )}
                  >
                    {labels[t]}
                    {active && (
                      <span className="absolute left-1/2 -translate-x-1/2 -bottom-2 h-0.5 w-10 bg-blue-600 rounded" />
                    )}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Section header row */}
          <div className="px-3 py-2.5 border-b">
            <div className="flex items-center justify-between">
              <div className="text-base md:text-lg font-semibold"></div>
              {leftTab === "rankings" && !uhhpTop50 && (
                <label className="text-sm inline-flex items-center gap-2">
                  <input type="checkbox" />
                  <span>Show Drafted</span>
                </label>
              )}
            </div>

            {leftTab === "rankings" && null}
          </div>

          {/* Content area */}
          <div className="h-[calc(100vh-56px-32px)] overflow-auto">
            {leftTab === "rankings" && (
              <>
                {/* Detached sticky header for rankings list */}
                <div className="sticky top-0 z-10 bg-white border-y">
                  <div className="grid grid-cols-[28px_1fr_60px] items-center px-3 py-2">
                    <div className="text-[12px] font-semibold text-slate-500">{uhhpTop50 ? "Pick" : "Rank"}</div>
                    <div className="text-[12px] font-semibold text-slate-500">Player</div>
                    <div className="text-[12px] font-semibold text-slate-500 text-right inline-flex items-center justify-end gap-1">
                      {uhhpTop50 ? "Won" : "Pick Predictor"}
                    </div>
                  </div>
                </div>

                {/* Rows */}
                <div className="h-[calc(100vh-56px-32px-90px)] overflow-auto">
                  {uhhpFilled50
                    ? uhhpFilled50.map((entry, idx) => (
                        <div
                          key={`${entry.kind}-${idx}`}
                          className={cn(
                            "grid grid-cols-[28px_1fr_60px] items-start px-3 py-2 border-b hover:bg-slate-50",
                            idx + 1 === currentPickNum ? "bg-blue-50 border-blue-300" : "",
                          )}
                        >
                          {/* Pick number */}
                          <div className="flex items-center gap-1.5 text-[12px] text-slate-700 pt-0.5">
                            <span className="tabular-nums">{idx + 1}.</span>
                          </div>

                          {/* Player info */}
                          <div className="min-w-0">
                            {entry.kind === "taken" ? (
                              <>
                                {(() => {
                                  const r = entry.data
                                  return (
                                    <>
                                      <button
                                        type="button"
                                        onClick={() => openPlayer({
                                          id: r.player,
                                          name: r.player,
                                          team: "",
                                          pos: r.pos || "",
                                          bye: 0,
                                          overall: idx + 1,
                                          adp: idx + 1,
                                          expertPct: 0,
                                        })}
                                        className="font-semibold leading-snug text-[13px] break-words text-left hover:underline focus:outline-none focus:underline"
                                      >
                                        {r.player}
                                      </button>
                                      <div className="mt-1 flex items-center gap-2">
                                        <span
                                          className={cn(
                                            "inline-flex items-center rounded-full px-1.5 py-[2px] text-[10px] font-semibold",
                                            posPillClass(r.pos || ""),
                                          )}
                                        >
                                          {r.pos || ""}
                                        </span>
                                        <div className="text-[12px] text-slate-600 break-words">{r.team}</div>
                                      </div>
                                    </>
                                  )
                                })()}
                              </>
                            ) : entry.kind === "nominated" ? (
                              <>
                                <div className="font-semibold leading-snug text-[13px] break-words text-left">
                                  {entry.data?.player}
                                </div>
                                <div className="mt-1 flex items-center gap-2">
                                  <span
                                    className={cn(
                                      "inline-flex items-center rounded-full px-1.5 py-[2px] text-[10px] font-semibold",
                                      posPillClass(entry.data?.pos || ""),
                                    )}
                                  >
                                    {entry.data?.pos || ""}
                                  </span>
                                  <div className="text-[12px] text-slate-600 break-words">{entry.team}</div>
                                </div>
                              </>
                            ) : (
                              <>
                                <div className="text-[12px] text-slate-600 break-words">{entry.team}</div>
                              </>
                            )}
                          </div>

                          {/* Winning bid */}
                          {entry.kind === "taken" ? (
                            (() => {
                              const r = entry.data
                              const key = (r.player || "").toString().trim().toLowerCase()
                              const fp = fpMap[key]
                              const priceStr = `$${r.price}`
                              return (
                                <div className="self-center text-right pr-1">
                                  <div className="text-sm font-semibold text-emerald-600">{priceStr}</div>
                                </div>
                              )
                            })()
                          ) : entry.kind === "nominated" ? (
                            <div className="self-center text-right pr-1 text-slate-400 text-sm">—</div>
                          ) : (
                            <div className="self-center text-right pr-1 text-slate-400 text-sm">—</div>
                          )}
                        </div>
                      ))
                    : rankings.map((p, idx) => (
                    <div
                      key={p.id}
                          className="grid grid-cols-[28px_1fr_60px] items-start px-3 py-2 border-b hover:bg-slate-50"
                    >
                      {/* Rank + star (tight spacing) */}
                      <div className="flex items-center gap-1.5 text-[12px] text-slate-700 pt-0.5">
                        <span className="tabular-nums">{idx + 1}.</span>
                        <Star className="w-3.5 h-3.5 text-slate-300" />
                      </div>

                      {/* Player info (compact, stacked) */}
                      <div className="min-w-0">
                        <button
                          type="button"
                          onClick={() => openPlayer(p)}
                          className="font-semibold leading-snug text-[13px] break-words text-left hover:underline focus:outline-none focus:underline"
                        >
                          {p.name}
                        </button>
                        <div className="mt-1 flex items-center gap-2">
                          <span
                            className={cn(
                              "inline-flex items-center rounded-full px-1.5 py-[2px] text-[10px] font-semibold",
                              posPillClass(p.pos),
                            )}
                          >
                            {p.pos}
                          </span>
                          <div className="text-[12px] text-slate-600 break-words">
                            {p.team} <span className="text-slate-400">(Bye {p.bye})</span>
                          </div>
                        </div>
                      </div>

                      {/* Pick % */}
                      <div className="text-right text-[13px] font-bold text-rose-600 pr-1">{p.expertPct}%</div>
                    </div>
                  ))}
                </div>
              </>
            )}

            

            {leftTab === "queue" && (
              <div className="p-3 space-y-3">
                <div>
                  <div className="text-sm font-semibold mb-1">Current Tie-Break Order</div>
                  <ol className="space-y-1 text-sm">
                    {(auctionOrder || []).map((n, i) => (
                      <li key={`${n}-${i}`} className="flex items-center gap-2">
                        <span className="w-6 text-right tabular-nums text-slate-500">{i + 1}.</span>
                        <span>{n}</span>
                      </li>
                    ))}
                  </ol>
                    </div>
                <div>
                  <div className="text-sm font-semibold mb-1">Tie-Break Audit Log</div>
                  <div className="rounded border divide-y">
                    {(tieAudit || []).length === 0 && (
                      <div className="px-3 py-2 text-xs text-slate-500">No tie-breaks yet.</div>
                    )}
                    {(tieAudit || []).map((t, i) => (
                      <div key={i} className="px-3 py-2 text-xs">
                        <div className="font-medium">Pick #{t.pick}</div>
                        <div>Contenders: {t.winners.join(", ")}</div>
                        <div>Advantage: {t.advantage || "—"}</div>
                  </div>
                    ))}
                </div>
              </div>
              </div>
            )}
          </div>
        </aside>

        {/* Middle: Suggestions and tabs */}
        <section className="bg-white">
          {/* Bidding Controls */
          }
          <div className="pt-0">
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 mb-3 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-14 h-14 rounded bg-slate-200 overflow-hidden">
                    {nominated ? (
                      <Image
                        src={"/placeholder.svg?height=64&width=64&query=hockey%20player%20headshot"}
                        alt={nominated.player}
                        width={56}
                        height={56}
                      />
                    ) : null}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-semibold">
                      {nominated ? nominated.player : "Bidding Controls"}
                    </div>
                    <div className="text-xs text-slate-500">
                      {nominated ? (
                        (() => {
                          const key = (nominated.player || "").toString().trim().toLowerCase()
                          const ageVal = ageMap[key]
                          const ageStr = typeof ageVal === "number" ? String(ageVal) : "—"
                          const faStr = (nominated.type || "").toString().toUpperCase() || "—"
                          return (
                            <>
                              {nominated.pos} • {ageStr} • {faStr}
                            </>
                          )
                        })()
                      ) : (
                        "Select a player and place your bid"
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {(() => {
                    const isRfa = (nominated?.type || "").toString().toUpperCase() === "RFA"
                    const key = (nominated?.player || "").toString().trim().toLowerCase()
                    const rfaTaken = (uhhpPicks || []).some((r: any) => ((r?.player || "").toString().trim().toLowerCase()) === key)
                    const canAct = isRfa && rfaTaken
                    return (
                      <div className="flex items-center gap-2 mr-2">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={!canAct}
                          className={cn(!canAct ? "opacity-50 text-slate-400" : undefined)}
                          onClick={() => toast.message("RFA Matched")}
                        >
                          Match
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={!canAct}
                          className={cn(!canAct ? "opacity-50 text-slate-400" : undefined)}
                          onClick={() => toast.message("RFA Released")}
                        >
                          Release
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className={cn("ml-1", (!nominated || (revealed && !tieTeams.includes(yourTeamId))) ? "opacity-50 cursor-not-allowed" : undefined)}
                          disabled={!nominated || (revealed && !tieTeams.includes(yourTeamId))}
                          onClick={() => {
                            if (!nominated) { toast.message("Nominate a player first"); return }
                            if (revealed && !tieTeams.includes(yourTeamId)) return
                            setBidAmount("0")
                            const key = (nominated.player || "").toString().trim().toLowerCase()
                            const fp = typeof (nominated as any).fp === "number" ? (nominated as any).fp : fpMap[key]
                            const base = typeof fp === "number" ? Math.max(2, Math.min(60, Math.round(fp / 20))) : 8
                            const nextBids: Record<string, number> = { [yourTeamId]: 0 }
                            for (const t of teams) {
                              if (t.id === yourTeamId) continue
                              const jitter = Math.floor((Math.random() * 7) - 3)
                              const b = Math.max(2, Math.min(100, base + jitter))
                              nextBids[t.id] = b
                            }
                            setGmBids(nextBids)
                            const all: Record<string, boolean> = {}
                            for (const t of teams) all[t.id] = true
                            setBidSubmitted(all)
                            // start reveal countdown explicitly in case effect timing misses
                            setRevealed(false)
                            setRevealTimer(3)
                            toast.message("Passed (bid $0)")
                          }}
                        >
                          Pass
                        </Button>
                      </div>
                    )
                  })()}
                  <div className="relative">
                    <span className="absolute left-1.5 top-1/2 -translate-y-1/2 text-xs text-slate-500">$</span>
                    <Input
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      className="w-12 h-8 pl-4 text-center"
                      value={bidAmount}
                      onChange={(e) => {
                        const raw = e.target.value
                        const cleaned = raw.replace(/[^0-9]/g, "")
                        setBidAmount(cleaned)
                      }}
                      onBlur={() => {
                        const n = Math.floor(Number(bidAmount || "0"))
                        setBidAmount(String(Math.max(2, Number.isFinite(n) ? n : 2)))
                      }}
                      placeholder="2"
                    />
                  </div>
                  {(() => {
                    const isSubmitted = !!bidSubmitted[yourTeamId]
                    const youInTie = revealed && tieTeams.includes(yourTeamId)
                    const disabled = !nominated || (revealed && !youInTie)
                    const showCancelHover = !revealed && isSubmitted
                    const label = youInTie ? "Re-Bid" : (isSubmitted ? (showCancelHover ? "Cancel" : "Submitted") : "Submit Bid")
                    const baseCls = "ml-2"
                    const stateCls = youInTie
                      ? "bg-orange-500 hover:bg-orange-600 text-white"
                      : isSubmitted
                        ? (showCancelHover
                            ? "bg-rose-600 hover:bg-rose-700 text-white"
                            : "bg-emerald-600/10 text-emerald-700 border border-emerald-300 hover:bg-emerald-600/20")
                        : undefined
                    return (
                      <Button
                        className={cn(baseCls, stateCls, disabled ? "opacity-50 cursor-not-allowed" : undefined)}
                        disabled={disabled}
                        onMouseEnter={() => { if (!revealed) setSubmittedHover(true) }}
                        onMouseLeave={() => { if (!revealed) setSubmittedHover(false) }}
                        onClick={() => {
                          if (!nominated) return
                          if (revealed) {
                            if (!youInTie) return
                            // Re-bid submission for tie-break
                            const amt = Math.max(2, Math.floor(Number(bidAmount || "0")))
                            setGmBids((prev) => ({ ...prev, [yourTeamId]: amt }))
                            const all: Record<string, boolean> = {}
                            for (const t of teams) all[t.id] = true
                            setBidSubmitted(all)
                            setRevealed(false)
                            setRevealTimer(3)
                            toast.success(`Re-bid $${amt}`)
                            return
                          }
                          const isSub = !!bidSubmitted[yourTeamId]
                          if (isSub) {
                            setBidSubmitted((prev) => ({ ...prev, [yourTeamId]: false }))
                            setGmBids((prev) => { const cp = { ...prev }; delete cp[yourTeamId]; return cp })
                            toast.message("Bid cancelled")
                          } else {
                            const amt = Math.max(2, Math.floor(Number(bidAmount || "0")))
                            toast.success(`Bid $${amt} on ${nominated?.player || ""}`)
                            setBidSubmitted((prev) => ({ ...prev, [yourTeamId]: true }))
                            // generate bids for all GMs this round
                            const key = (nominated.player || "").toString().trim().toLowerCase()
                            const fp = typeof (nominated as any).fp === "number" ? (nominated as any).fp : fpMap[key]
                            const base = typeof fp === "number" ? Math.max(2, Math.min(60, Math.round(fp / 20))) : 8
                            const nextBids: Record<string, number> = { [yourTeamId]: amt }
                            for (const t of teams) {
                              if (t.id === yourTeamId) continue
                              const jitter = Math.floor((Math.random() * 7) - 3)
                              const b = Math.max(2, Math.min(100, base + jitter))
                              nextBids[t.id] = b
                            }
                            setGmBids(nextBids)
                            const all: Record<string, boolean> = {}
                            for (const t of teams) all[t.id] = true
                            setBidSubmitted(all)
                          }
                        }}
                      >
                        {label}
                      </Button>
                    )
                  })()}
                </div>
                
              </div>
              {/* GM bid status */}
              <div className="mt-3">
                <div className="text-xs text-slate-500 mb-1">GM Bids {revealTimer !== null ? `(revealing in ${revealTimer}s)` : revealed ? "(revealed)" : ""}</div>
                <div className="flex items-center gap-3 overflow-x-auto whitespace-nowrap py-1">
                  {teams.map((t) => {
                    const submitted = !!bidSubmitted[t.id]
                    const bid = gmBids[t.id]
                    const isTie = revealed && tieTeams.includes(t.id)
                    const hasAdv = revealed && tieAdvantageTeamId === t.id && isTie
                    return (
                      <div key={t.id} className="inline-flex items-center flex-col">
                        <div
                          className={cn(
                            "w-12 h-12 rounded-full flex items-center justify-center text-[12px] font-bold",
                            submitted && !revealed ? "bg-emerald-500 text-white" : "bg-slate-200 text-slate-700",
                            isTie ? "bg-orange-400 text-white" : undefined,
                            hasAdv ? "ring-2 ring-orange-700" : undefined,
                          )}
                          title={t.name}
                        >
                          {teamAbbr(t.name)}
                        </div>
                        {revealed && (
                          <div className="mt-1 text-[11px] text-slate-600 tabular-nums">{bid != null ? `$${bid}` : "—"}</div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>
          <div className="border-b">
            <Tabs defaultValue="myteam">
              <div className="flex items-center justify-between">
                <TabsList className="bg-transparent p-0">
                  {[
                    { val: "myteam", label: "My Team" },
                    { val: "cap", label: "Cap Summary" },
                    { val: "cheatsheets", label: "Cheat Sheet" },
                    { val: "history", label: "Bid History" },
                  ].map((t) => (
                    <TabsTrigger
                      key={t.val}
                      value={t.val}
                      className="rounded-none border-b-2 border-transparent text-slate-600 data-[state=active]:border-blue-600 data-[state=active]:text-blue-700 data-[state=active]:font-semibold"
                    >
                      {t.label}
                    </TabsTrigger>
                  ))}
                </TabsList>

                <div className="hidden md:flex items-center gap-2 py-2" />
              </div>

              <TabsContent value="history" className="mt-3">
                <div className="px-2 pb-3">
                  <h2 className="text-xl font-bold mb-3">Bid History</h2>
                  <div className="rounded-lg border overflow-auto">
                    <table className="min-w-full text-sm">
                      <thead className="bg-slate-50 text-slate-600">
                        <tr>
                          <th className="text-left px-3 py-2">Nominator</th>
                          <th className="text-left px-3 py-2">Winner</th>
                          {teams.map((t) => (
                            <th key={t.id} className="text-right px-2 py-2 whitespace-nowrap">{teamAbbr(t.name)}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(uhhpPicks || []).slice(0, 24).map((r: any, i: number) => (
                          <tr key={i} className="border-t">
                            <td className="px-3 py-2 text-slate-700">{r.team || "—"}</td>
                            <td className="px-3 py-2 font-semibold">{r.player ? `${r.player} $${r.price}` : "—"}</td>
                            {teams.map((t) => {
                              // show placeholder bids for already completed rows
                              let bid: number | undefined
                              if (i === 0 && revealed) {
                                bid = gmBids[t.id]
                              } else if (i > 0 && r.player) {
                                // generate deterministic pseudo-bids based on row/team for testing
                                const seed = (i + 1) * (t.id.charCodeAt(0))
                                const base = Math.max(2, Math.min(30, 6 + ((seed % 9))))
                                // ensure winner has highest in that row
                                const isWinner = teamAbbr(r.team) === teamAbbr(t.name)
                                bid = isWinner ? r.price : base
                              }
                              return (
                                <td key={t.id} className="px-2 py-2 text-right tabular-nums text-slate-600">{bid != null ? `$${bid}` : "—"}</td>
                              )
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="myteam" className="p-4">
                {(() => {
                  // Table: render rows by required slots (2xC, 3xW, 4xF, 4xD, 2xG)
                  const REQUIRED_ROWS: Array<{ label: string; count: number }> = [
                    { label: "C", count: 2 },
                    { label: "W", count: 3 },
                    { label: "F", count: 4 },
                    { label: "D", count: 4 },
                    { label: "G", count: 2 },
                  ]
                  const myTeamName = selectedTeamName || "New Oilers Nation"
                  const youAbbr = teamAbbr(myTeamName)
                  const stage1Roster = (() => {
                    const t = (stage1Teams || []).find((tt: any) => (tt?.team_name || "") === myTeamName)
                    const players: any[] = (t?.players as any[]) || []
                    return players
                  })()
                  const wonPlayers = (uhhpPicks || []).filter((r: any) => teamAbbr(r.team || "") === youAbbr && r.player)
                  const myPicks = wonPlayers.length ? wonPlayers : stage1Roster.map((p: any) => ({
                    player: p?.player || p?.player_full_name || p?.display_name,
                    pos: p?.pos,
                    price: p?.salary || 0,
                    years: p?.years,
                    future_fa: p?.future_fa,
                    team: myTeamName,
                  }))
                  const byPos: Record<string, any[]> = { C: [], W: [], F: [], D: [], G: [] }
                  const reserves: any[] = []
                  for (const r of myPicks) {
                    const nameKey = normalizeName(r.player)
                    if (benchSet.has(nameKey)) {
                      reserves.push(r)
                      continue
                    }
                    const posRaw = (r.pos || "").toString().toUpperCase()
                    const key = posRaw === "LW" || posRaw === "RW" ? "W" : (byPos[posRaw] ? posRaw : "F")
                    byPos[key].push(r)
                  }
                  function take(pos: string) {
                    const pl = byPos[pos].shift() || null
                    return pl
                  }
                  // Compute totals for header metrics
                  const byPosForTotals: Record<string, any[]> = {
                    C: [...byPos.C],
                    W: [...byPos.W],
                    F: [...byPos.F],
                    D: [...byPos.D],
                    G: [...byPos.G],
                  }
                  let totalSalary = 0
                  let budgetBids = 0
                  for (const row of REQUIRED_ROWS) {
                    for (let i = 0; i < row.count; i++) {
                      const sim = (byPosForTotals[row.label] || []).shift() || null
                      if (sim) {
                        totalSalary += sim?.price ? Number(sim.price) : 0
                      } else {
                        const slotId = `${row.label}-${i}`
                        const bid = parseInt((targets[slotId]?.bid || "0") as string, 10) || 0
                        budgetBids += bid
                      }
                    }
                  }
                  // Include reserve players (benched + overflow)
                  const reservesForTotals = [
                    ...reserves,
                    ...byPosForTotals.C,
                    ...byPosForTotals.W,
                    ...byPosForTotals.F,
                    ...byPosForTotals.D,
                    ...byPosForTotals.G,
                  ]
                  for (const r of reservesForTotals) {
                    totalSalary += r?.price ? Number(r.price) : 0
                  }
                  const totalBudgeted = totalSalary + budgetBids
                  return (
                    <>
                      <div className="mb-3 flex items-center justify-end gap-6">
                        <div className="text-sm">
                          <span className="text-slate-500">Salary: </span>
                          <span className="font-semibold tabular-nums">{`$${totalSalary}`}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-slate-500">Budgeted: </span>
                          <span className="font-semibold tabular-nums">{`$${totalBudgeted}`}</span>
                        </div>
                      </div>
                      <div className="rounded-lg border">
                        <div className="grid grid-cols-[60px_minmax(0,1fr)_70px_100px_100px_110px] items-stretch border-b bg-slate-50 text-xs font-semibold text-slate-600">
                          <div className="px-3 py-2">Pos</div>
                          <div className="px-3 py-2">Player</div>
                          <div className="px-3 py-2 text-center">Status</div>
                          <div className="px-3 py-2 text-center">Pro FTPS</div>
                          <div className="px-3 py-2 text-center">Contract</div>
                          <div className="px-3 py-2 text-center">Salary</div>
                        </div>
                        <div>
                          {REQUIRED_ROWS.flatMap((row) =>
                            Array.from({ length: row.count }, (_, i) => (
                              <div key={`${row.label}-${i}`} className="grid grid-cols-[60px_minmax(0,1fr)_70px_100px_100px_110px] items-center border-b">
                                <div className="px-3 py-2 text-xs font-semibold text-slate-600">{row.label}</div>
                                {(() => {
                                  const pl = take(row.label)
                                  const slotId = `${row.label}-${i}`
                                  if (!pl) {
                                    const eligiblePositions = row.label === "F" ? ["C", "W"] : [row.label]
                                    const takenSet = new Set<string>()
                                    ;(uhhpPicks || []).forEach((r: any) => {
                                      if (Number(r?.price) > 0) takenSet.add(((r?.player || "").toString().trim().toLowerCase()))
                                    })
                                    const options = (projections || [])
                                      .filter((p) => eligiblePositions.includes(((p.pos || "").toString().toUpperCase())))
                                      .filter((p) => !takenSet.has(((p.player || "").toString().trim().toLowerCase())))
                                      .slice(0, 50)
                                    const tgt = targets[slotId]
                                    const fp = (() => {
                                      if (tgt?.player) {
                                        const v = typeof tgt.player.fp === "number" ? tgt.player.fp : fpMap[normalizeName(tgt.player.player)]
                                        return typeof v === "number" ? v.toFixed(1) : "—"
                                      }
                                      return "—"
                                    })()
                                    const handleSuggest = () => {
                                      // Avoid previously targeted players in any slot
                                      const selectedNames = new Set(
                                        Object.values(targets)
                                          .map((t) => normalizeName(t?.player?.player))
                                          .filter(Boolean) as string[],
                                      )
                                      const budget = parseInt(String(targets[slotId]?.bid || "0"), 10) || 0
                                      const withPrices = options
                                        .filter((p: any) => !selectedNames.has(normalizeName(p.player)))
                                        .map((p: any) => {
                                          const fpv = typeof p.fp === "number" ? p.fp : (fpMap[normalizeName(p.player)] || 0)
                                          const price = Math.max(2, Math.min(30, Math.round((fpv || 0) / 18)))
                                          return { p, fp: fpv, price }
                                        })
                                      const pool = budget > 0 ? withPrices.filter((x) => x.price <= budget) : withPrices
                                      if (!pool.length) return
                                      const best = pool.sort((a, b) => (b.fp - a.fp))[0]
                                      setTargets((prev) => ({
                                        ...prev,
                                        [slotId]: {
                                          player: best.p,
                                          // Never override a user's entered number; keep whatever is there
                                          bid: prev[slotId]?.bid || "",
                                        },
                                      }))
                                    }
                                    return (
                                      <>
                                        <div className="px-3 py-2">
                                          {tgt?.player ? (
                                            <div className="flex items-center gap-2 min-w-0">
                                              <Select
                                                value={tgt?.player?.player || undefined}
                                                onValueChange={(v) => {
                                                  const sel = (projections || []).find((p) => (p.player || "") === v) || null
                                                  setTargets((prev) => ({ ...prev, [slotId]: { player: sel, bid: prev[slotId]?.bid || "" } }))
                                                }}
                                              >
                                                <SelectTrigger className="h-7 px-2 text-xs w-[160px]">
                                                  <SelectValue />
                                                </SelectTrigger>
                                                <SelectContent>
                                                  {options.map((p: any, idx: number) => (
                                                    <SelectItem key={`${slotId}-opt-${idx}`} value={String(p.player)}>
                                                      {p.player} ({p.pos}) • {(typeof p.fp === "number" ? p.fp.toFixed(1) : (fpMap[normalizeName(p.player)] ?? "—"))}{typeof p.fp === "number" || fpMap[normalizeName(p.player)] != null ? " FP" : ""}
                                                    </SelectItem>
                                                  ))}
                                                </SelectContent>
                                              </Select>
                                              <button
                                                className="text-xs text-slate-500 hover:text-slate-700"
                                                onClick={() => setTargets((prev) => ({ ...prev, [slotId]: { player: null, bid: prev[slotId]?.bid || "" } }))}
                                                aria-label="Remove target"
                                                title="Remove"
                                              >
                                                <X className="w-3.5 h-3.5" />
                  </button>
                                            </div>
                                          ) : (
                                            <div className="flex items-center gap-2 min-w-0">
                                              <Select
                                                value={tgt?.player?.player || undefined}
                                                onValueChange={(v) => {
                                                  const sel = (projections || []).find((p) => (p.player || "") === v) || null
                                                  setTargets((prev) => ({ ...prev, [slotId]: { player: sel, bid: prev[slotId]?.bid || "" } }))
                                                }}
                                              >
                                                <SelectTrigger className="h-7 px-2 text-xs w-[120px]">
                                                  <SelectValue placeholder="Pick" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                  {options.map((p: any, idx: number) => (
                                                    <SelectItem key={`${slotId}-opt-${idx}`} value={String(p.player)}>
                                                      {p.player} ({p.pos}) • {(typeof p.fp === "number" ? p.fp.toFixed(1) : (fpMap[normalizeName(p.player)] ?? "—"))}{typeof p.fp === "number" || fpMap[normalizeName(p.player)] != null ? " FP" : ""}
                                                    </SelectItem>
                                                  ))}
                                                </SelectContent>
                                              </Select>
                                              <button className="text-xs text-blue-600 hover:underline" onClick={handleSuggest}>Suggest player</button>
                                            </div>
                                          )}
                                        </div>
                                        <div className="px-3 py-2 text-sm text-center">{(() => {
                                          const raw = ((tgt?.player?.type || "").toString().toUpperCase())
                                          return raw === "UFA" || raw === "RFA" ? raw : "—"
                                        })()}</div>
                                        <div className="px-3 py-2 text-sm tabular-nums text-center">{fp}</div>
                                        <div className="px-3 py-2 text-sm text-slate-400 text-center">—</div>
                                        <div className="px-3 py-2 flex justify-center">
                                          <div className="relative">
                                            <span className="absolute left-1.5 top-1/2 -translate-y-1/2 text-xs text-slate-500">$</span>
                                            <Input
                                               inputMode="numeric"
                                               pattern="[0-9]*"
                                               placeholder="0"
                                               value={tgt?.bid || ""}
                                               onChange={(e) => {
                                                 const raw = e.target.value || ""
                                                 const digits = raw.replace(/[^0-9]/g, "")
                                                 setTargets((prev) => ({ ...prev, [slotId]: { player: prev[slotId]?.player || null, bid: digits } }))
                                               }}
                                               className="h-8 w-[72px] pl-4 text-center"
                                            />
                                          </div>
                                        </div>
                                      </>
                                    )
                                  }
                                  const playerName = pl.player
                                  const price = pl.price ?? 0
                                  const contractStr = (() => {
                                    const years = pl.years || pl.contractYears
                                    const fa = pl.future_fa
                                    if (years) return `${years}y`
                                    if (fa) return String(fa)
                                    return "—"
                                  })()
                                  const fpKey = (playerName || "").toString().trim().toLowerCase()
                                  let fpVal = typeof fpMap[fpKey] === "number" ? fpMap[fpKey] : undefined
                                  if (fpVal == null) {
                                    const proj = (projections || []).find((p: any) => ((p.player || "").toString().trim().toLowerCase()) === fpKey)
                                    if (proj && typeof (proj as any).fp === "number") {
                                      fpVal = (proj as any).fp
                                    }
                                  }
                                  const fpStr = fpVal != null ? fpVal.toFixed(1) : "—"
                                  const statusStr = (() => {
                                    const raw = ((pl as any).type || (pl as any).fa_type || (pl as any).future_fa || "").toString().toUpperCase()
                                    return raw === "UFA" || raw === "RFA" ? raw : "—"
                                  })()
                                  const posDisp = (pl.pos || "").toString().toUpperCase()
                                  return (
                                    <>
                                      <div className="px-3 py-2">
                                        <div className="flex items-center gap-2 min-w-0">
                                          <div className="font-medium text-sm truncate">{playerName}</div>
                                          <button
                                            className="h-6 px-2 text-[11px] rounded border hover:bg-slate-50"
                                            onClick={() => toggleBench(playerName)}
                                            title="Move to Reserves"
                                          >
                                            Sit
                  </button>
                                          <span className="ml-2 text-xs text-slate-500">{posDisp}</span>
                                        </div>
                                      </div>
                                      <div className="px-3 py-2 text-sm text-center">{statusStr}</div>
                                      <div className="px-3 py-2 text-sm tabular-nums text-center">{fpStr}</div>
                                      <div className="px-3 py-2 text-sm text-center">{contractStr}</div>
                                      <div className="px-3 py-2 text-sm font-semibold tabular-nums text-center">{`$${price}`}</div>
                                    </>
                                  )
                                })()}
                              </div>
                            )),
                          )}
                          {(() => {
                            reserves.push(...byPos.C, ...byPos.W, ...byPos.F, ...byPos.D, ...byPos.G)
                            if (!reserves.length) {
                              return (
                                <div className="grid grid-cols-[60px_minmax(0,1fr)_70px_100px_100px_110px] items-center">
                                  <div className="px-3 py-2 text-xs font-semibold text-slate-600">Res</div>
                                  <div className="px-3 py-2 text-sm text-slate-400">None</div>
                                  <div className="px-3 py-2" />
                                  <div className="px-3 py-2" />
                                  <div className="px-3 py-2" />
                                  <div className="px-3 py-2" />
                                </div>
                              )
                            }
                            return reserves.map((r, i) => {
                              const playerName = r.player
                              const price = r.price ?? 0
                              const contractStr = (() => {
                                const years = r.years || r.contractYears
                                const fa = r.future_fa
                                if (years) return `${years}y`
                                if (fa) return String(fa)
                                return "—"
                              })()
                              const fpKey = (playerName || "").toString().trim().toLowerCase()
                              let fpVal = typeof fpMap[fpKey] === "number" ? fpMap[fpKey] : undefined
                              if (fpVal == null) {
                                const proj = (projections || []).find((p: any) => ((p.player || "").toString().trim().toLowerCase()) === fpKey)
                                if (proj && typeof (proj as any).fp === "number") {
                                  fpVal = (proj as any).fp
                                }
                              }
                              const fpStr = fpVal != null ? fpVal.toFixed(1) : "—"
                              const statusStr = (() => {
                                const raw = ((r as any).type || (r as any).fa_type || (r as any).future_fa || "").toString().toUpperCase()
                                return raw === "UFA" || raw === "RFA" ? raw : "—"
                              })()
                              const posDisp = (r.pos || "").toString().toUpperCase()
                              return (
                                <div key={i} className="grid grid-cols-[60px_minmax(0,1fr)_70px_100px_100px_110px] items-center border-b">
                                  <div className="px-3 py-2 text-xs font-semibold text-slate-600">Res</div>
                                  <div className="px-3 py-2">
                                    <div className="flex items-center gap-2 min-w-0">
                                      <button
                                        className="h-6 px-2 text-[11px] rounded border hover:bg-slate-50"
                                        onClick={() => toggleBench(playerName)}
                                        title="Move to Active"
                                      >
                                        Res
                  </button>
                                      <div className="font-medium text-sm truncate">{playerName}</div>
                                      <span className="ml-2 text-xs text-slate-500">{posDisp}</span>
                </div>
              </div>
                                  <div className="px-3 py-2 text-sm text-center">{statusStr}</div>
                                  <div className="px-3 py-2 text-sm tabular-nums text-center">{fpStr}</div>
                                  <div className="px-3 py-2 text-sm text-center">{contractStr}</div>
                                  <div className="px-3 py-2 text-sm font-semibold tabular-nums text-center">{`$${price}`}</div>
                                </div>
                              )
                            })
                          })()}
                        </div>
                      </div>
                    </>
                  )
                })()}
              </TabsContent>

              <TabsContent value="cap" className="p-4">
                {(() => {
                  const teamsList = (stage1Teams || []).map((t: any) => ({
                    name: t?.team_name || t?.team || t?.name,
                    players: (t?.players as any[]) || [],
                  }))
                  const REQUIRED: Record<string, number> = { C: 2, W: 3, F: 4, D: 4, G: 2 }
                  const tiles = teamsList.map((t) => {
                    const counts: Record<string, number> = { C: 0, W: 0, F: 0, D: 0, G: 0 }
                    let salary = 0
                    let unsignedRfas = 0
                    for (const p of t.players) {
                      const pos = (p?.pos || "").toString().toUpperCase()
                      if (pos in counts) counts[pos] += 1
                      const pay = Number(p?.salary || 0)
                      salary += pay
                      const typeStr = (p?.type || p?.status || p?.fa_status || p?.future_fa || "").toString().toUpperCase()
                      const isRfa = typeStr === "RFA"
                      const isUnsigned = pay === 0
                      if (isRfa && isUnsigned) unsignedRfas += 1
                    }
                    // Contracted per slot (cap to required)
                    const contractedC = Math.min(counts.C, REQUIRED.C)
                    const contractedW = Math.min(counts.W, REQUIRED.W)
                    const contractedD = Math.min(counts.D, REQUIRED.D)
                    const contractedG = Math.min(counts.G, REQUIRED.G)
                    const forwardEligible = counts.C + counts.W
                    const extraForF = Math.max(0, forwardEligible - REQUIRED.C - REQUIRED.W)
                    const contractedF = Math.min(REQUIRED.F, extraForF)
                    const contracted: Record<string, number> = {
                      C: contractedC,
                      W: contractedW,
                      F: contractedF,
                      D: contractedD,
                      G: contractedG,
                    }
                    const requiredNeeded =
                      (REQUIRED.C - contractedC) +
                      (REQUIRED.W - contractedW) +
                      (REQUIRED.F - contractedF) +
                      (REQUIRED.D - contractedD) +
                      (REQUIRED.G - contractedG)
                    const capSpace = Math.max(0, 100 - salary)
                    return { ...t, counts, contracted, salary, capSpace, unsignedRfas, requiredNeeded }
                  })
                  return (
                    <div className="grid gap-3 grid-cols-1 md:grid-cols-3">
                      {tiles.map((t) => {
                        const MAX_NAME = 16
                        const displayName = (() => {
                          const full = (t.name || "").toString()
                          if (full.length <= MAX_NAME) return full
                          const words = full.split(/\s+/).filter(Boolean)
                          let out = ""
                          for (const w of words) {
                            const candidate = out ? `${out} ${w}` : w
                            if (candidate.length > MAX_NAME) break
                            out = candidate
                          }
                          if (!out) out = full.slice(0, MAX_NAME)
                          return `${out}...`
                        })()
                        return (
                          <div key={t.name} className="rounded-lg border p-2 relative">
                            <div className="text-sm font-semibold mb-1 pr-12 whitespace-nowrap">{displayName}</div>
                          <div className="absolute right-2 top-2 text-sm text-slate-700">{`$${t.salary} / $100`}</div>
                          <div className="text-xs text-slate-600 grid grid-cols-5 gap-1 text-center">
                            <div className="flex flex-col items-center gap-0.5">
                              <div className="font-semibold">C</div>
                              <div className="tabular-nums">{t.contracted.C}/{REQUIRED.C}</div>
                            </div>
                            <div className="flex flex-col items-center gap-0.5">
                              <div className="font-semibold">W</div>
                              <div className="tabular-nums">{t.contracted.W}/{REQUIRED.W}</div>
                            </div>
                            <div className="flex flex-col items-center gap-0.5">
                              <div className="font-semibold">F</div>
                              <div className="tabular-nums">{t.contracted.F}/{REQUIRED.F}</div>
                            </div>
                            <div className="flex flex-col items-center gap-0.5">
                              <div className="font-semibold">D</div>
                              <div className="tabular-nums">{t.contracted.D}/{REQUIRED.D}</div>
                            </div>
                            <div className="flex flex-col items-center gap-0.5">
                              <div className="font-semibold">G</div>
                              <div className="tabular-nums">{t.contracted.G}/{REQUIRED.G}</div>
                            </div>
                            <div className="mt-1 text-xs text-slate-600 flex flex-col gap-0.5 w-full">
                              <span className="whitespace-nowrap">Unsigned RFAs: {t.unsignedRfas}</span>
                              <span className="whitespace-nowrap text-right">Players Req: {t.requiredNeeded}</span>
                            </div>
                          </div>
                        </div>
                        )
                      })}
                    </div>
                  )
                })()}
              </TabsContent>

              <TabsContent value="suggestions" className="mt-3">
                <div className="px-2 pb-3">
                  <h2 className="text-xl font-bold mb-3">Suggestions</h2>

                  <div className="space-y-3">
                    {suggestions.map((p) => (
                      <SuggestionRow
                        key={p.id}
                        p={p}
                        onDraft={() => draftPlayer(p)}
                        disabled={!isYouOnClock}
                        onOpen={(pp) => openPlayer(pp)}
                      />
                    ))}

                    <div className="flex justify-center pt-2">
                      <Button variant="outline" className="bg-transparent text-sm">
                        + Suggest Another Player
                      </Button>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="rankings" className="p-4 text-sm text-slate-600">
                Use the Rankings panel on the left to browse all players.
              </TabsContent>
              <TabsContent value="teams" className="p-4 text-sm text-slate-600">
                Teams/rosters view coming soon.
              </TabsContent>
              
              <TabsContent value="cheatsheets" className="p-4 text-sm text-slate-600">
                {projections ? (
                  (() => {
                    const takenSet = new Set<string>()
                    ;(uhhpPicks || []).forEach((r: any) => {
                      if (Number(r?.price) > 0) {
                        const key = normalizeName(r?.player)
                        if (key) takenSet.add(key)
                      }
                    })
                    return (
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        {(["C", "W", "D", "G"] as const).map((pos) => {
                          const list = (projections || [])
                            .filter((p: any) => {
                              const raw = (p?.pos || "").toString().toUpperCase()
                              const mapped = raw === "LW" || raw === "RW" ? "W" : raw
                              return mapped === pos
                            })
                            .sort((a: any, b: any) => Number(b?.fp || 0) - Number(a?.fp || 0))
                          return (
                            <div key={pos} className="rounded-lg border bg-white">
                              <div className="px-3 py-2 border-b font-semibold text-slate-700">{pos}</div>
                              <ol className="max-h-[60vh] overflow-auto divide-y">
                                {list.map((p: any, i: number) => {
                                  const full = (p?.player || p?.name || p?.player_full_name || "").toString()
                                  const name = abbreviatePlayerName(full)
                                  const isTaken = takenSet.has(normalizeName(full))
                                  const fp = Math.round(Number(p?.fp ?? 0))
                                  return (
                                    <li key={`${pos}-${full}-${i}`} className="px-3 py-1.5 flex items-center gap-2">
                                      <span className="w-6 text-right text-slate-500">{i + 1}.</span>
                                      <span className={cn("truncate", isTaken ? "line-through text-slate-400" : undefined)}>{name}</span>
                                      <span className={cn("ml-auto tabular-nums text-xs text-slate-700", isTaken ? "line-through text-slate-400" : undefined)}>{fp}</span>
                                    </li>
                                  )
                                })}
                              </ol>
                            </div>
                          )
                        })}
                      </div>
                    )
                  })()
                ) : (
                  <div className="text-slate-500">No projections loaded.</div>
                )}
              </TabsContent>
              
            </Tabs>
          </div>
        </section>

        {/* Right: Picks / On the clock */}
        <aside className="rounded-none border-l bg-white h-full flex flex-col min-h-0">
          <div className="p-3 border-b">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="text-sm font-semibold">Projections</div>
                <Select value={projectionSource} onValueChange={(v) => setProjectionSource(v as any)}>
                  <SelectTrigger className="h-7 px-2 py-1 text-xs w-auto min-w-[120px]">
                    <SelectValue placeholder="Avg Experts" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="avg_experts">Avg Experts</SelectItem>
                    <SelectItem value="clusters">Clusters</SelectItem>
                  </SelectContent>
                </Select>
          </div>
              <label className="text-xs inline-flex items-center gap-2">
                <input type="checkbox" checked={showAvailable} onChange={(e) => setShowAvailable(e.target.checked)} />
                <span>Hide Taken</span>
              </label>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <div className="inline-flex items-center gap-2 text-xs">
                {(["All", "C", "W", "D", "G"] as const).map((opt) => (
                  <button
                    key={opt}
                    onClick={() => setPosFilter(opt)}
                    className={cn(
                      "px-2 py-1 rounded border",
                      posFilter === opt ? "bg-blue-50 text-blue-700 border-blue-300" : "bg-white text-slate-600 hover:bg-slate-50",
                    )}
                  >
                    {opt}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2 text-xs">
                <Select value={faFilter} onValueChange={(v) => setFaFilter(v as any)}>
                  <SelectTrigger className="h-7 px-2 py-1 text-xs w-auto min-w-[56px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="All">All</SelectItem>
                    <SelectItem value="UFA">UFA</SelectItem>
                    <SelectItem value="RFA">RFA</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <div className="h-[calc(100vh-56px-32px)] overflow-auto p-3 space-y-3">

            {projections ? (
              <div className="space-y-2">
                {(() => {
                  const takenSet = new Set<string>()
                  ;(uhhpPicks || []).forEach((r: any) => {
                    if (Number(r?.price) > 0) takenSet.add(((r?.player || "").toString().trim().toLowerCase()))
                  })
                  return (
                    projections
                      .filter((p) => (posFilter === "All" ? true : ((p.pos || "").toString().toUpperCase() === posFilter)))
                      .filter((p) => (faFilter === "All" ? true : ((p.type || "").toString().toUpperCase() === faFilter)))
                      .filter((p) => (showAvailable ? !takenSet.has(((p.player || "").toString().trim().toLowerCase())) : true))
                      .map((p, i) => (
                  <div key={i} className="rounded-lg border p-3">
                    <div className="text-[11px] text-slate-500">
                      {(() => {
                        const key = (p.player || "").toString().trim().toLowerCase()
                        const faStr = (p.type || "").toString().toUpperCase() || "—"
                        if (faStr === "RFA") {
                          // Find owning team from stage1Teams
                          const ownerTeam = (() => {
                            const t = (stage1Teams || []).find((tt: any) =>
                              Array.isArray(tt?.players) && tt.players.some((pl: any) => normalizeName(pl?.player) === key)
                            )
                            return t?.team_name ? ` • ${t.team_name}` : ""
                          })()
                          return `RFA${ownerTeam}`
                        }
                        return faStr
                      })()}
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-sm">{p.player}</div>
                        <div className="text-xs text-slate-500">
                          {(() => {
                            const nhlTeam = (p.team || p.nhl_team || p.nhl || "").toString()
                            const label = nhlTeam || "—"
                            return (
                              <>
                                {p.pos} • {label}
                              </>
                            )
                          })()}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {(() => {
                          const key = (p.player || "").toString().trim().toLowerCase()
                          const fp = typeof p.fp === "number" ? p.fp : fpMap[key]
                          const fpStr = typeof fp === "number" ? fp.toFixed(1) : "—"
                          const projPrice = typeof fp === "number" ? Math.max(2, Math.min(22, Math.round(fp / 20))) : null
                          const priceStr = projPrice !== null ? `$${projPrice}` : "$—"
                          return (
                            <div className="flex flex-col items-end mr-1 leading-tight">
                              <div className="text-sm font-semibold text-slate-700">{fpStr}</div>
                              <div className="text-sm font-semibold text-slate-700">{priceStr}</div>
                            </div>
                          )
                        })()}
                        {(() => {
                          const key = (p.player || "").toString().trim().toLowerCase()
                          const match = (uhhpPicks || []).find((r: any) => ((r?.player || "").toString().trim().toLowerCase()) === key && Number(r?.price) > 0)
                          const taken = !!match
                          if (taken) {
                            const fp = typeof p.fp === "number" ? p.fp : fpMap[key]
                            const proj = typeof fp === "number" ? Math.max(2, Math.min(22, Math.round(fp / 20))) : null
                            const won = Number(match?.price)
                            if (proj == null) {
                              return (
                                <div className="h-7 px-2 rounded border text-xs font-semibold inline-flex items-center justify-center bg-slate-200">
                                  ${won}
                                </div>
                              )
                            }
                            const diff = won - proj
                            // Compute gradient step 0..1 relative to projection (percentage over/under), clamp at 1
                            const denom = Math.max(2, proj)
                            const t = Math.max(0, Math.min(1, Math.abs(diff) / denom))
                            const baseClasses = "h-7 px-2 rounded border text-xs font-semibold inline-flex items-center justify-center"
                            if (diff > 0) {
                              // overpay: green->red gradient intensity
                              const redIntensity = t >= 0.66 ? "bg-red-300 text-red-900 border-red-400" : t >= 0.33 ? "bg-red-200 text-red-800 border-red-300" : "bg-red-100 text-red-700 border-red-300"
                              return <div className={`${baseClasses} ${redIntensity}`}>${won}</div>
                            } else {
                              // under or equal: green shades; equal should be strongest green
                              const greenIntensity = diff === 0
                                ? "bg-green-300 text-green-900 border-green-400"
                                : (t >= 0.66 ? "bg-green-300 text-green-900 border-green-400" : t >= 0.33 ? "bg-green-200 text-green-800 border-green-300" : "bg-green-100 text-green-700 border-green-300")
                              return <div className={`${baseClasses} ${greenIntensity}`}>${won}</div>
                            }
                          }
                          return (
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 transition-colors hover:bg-blue-600 hover:text-white"
                              onClick={() => {
                                setNominated(p)
                                setBidSubmitted({})
                                setGmBids({})
                                setRevealed(false)
                                setRevealTimer(null)
                                setSubmittedHover(false)
                                setPhase("Submit Bid")
                                toast.success(`Picked ${p.player}`)
                              }}
                            >
                              Pick
                            </Button>
                          )
                        })()}
                      </div>
                    </div>
                  </div>
                      ))
                  )
                })()}
              </div>
            ) : (
              <>
            {picks.map((pk, i) => {
              const team = teams.find((t) => t.id === pk.teamId)!
              const isCurrent = i === currentIdx
              return (
                <div
                  key={pk.overall}
                  className={cn("rounded-lg border p-3", isCurrent ? "bg-blue-600/10 border-blue-600" : "bg-white")}
                >
                  <div className="text-[11px] text-slate-500">{team.name}</div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {pk.player ? (
                        <div className="w-8 h-8 rounded-full bg-slate-200 overflow-hidden">
                          <Image
                            src={
                              pk.player.headshot ||
                              "/placeholder.svg?height=64&width=64&query=hockey%20player%20headshot" ||
                              "/placeholder.svg" ||
                              "/placeholder.svg" ||
                              "/placeholder.svg" ||
                              "/placeholder.svg"
                            }
                            alt={pk.player.name}
                            width={32}
                            height={32}
                          />
                        </div>
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
                          <Clock className="w-4 h-4 text-slate-400" />
                        </div>
                      )}
                      <div>
                        <div className="font-medium text-sm">
                          {isCurrent && team.id === yourTeamId ? (
                            <span className="inline-flex items-center gap-2">
                              Your Pick! <Clock className="w-4 h-4 text-blue-600" />
                            </span>
                          ) : pk.player ? (
                            pk.player.name
                          ) : (
                            "Waiting..."
                          )}
                        </div>
                        <div className="text-xs text-slate-500">
                          {pk.player ? (
                            <>
                              {pk.player.pos} • {pk.player.team}
                            </>
                          ) : (
                            <>
                                  Pick {pk.overall} • {team.needs?.length ? `Team needs ${team.needs.join(" ")}` : "On clock"}
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="text-xs text-slate-500">1.{String(pk.pickInRound).padStart(2, "0")}</div>
                  </div>
                </div>
              )
            })}

            <div className="text-xs uppercase tracking-wide text-slate-500 px-2 pt-2">Rd 2</div>
            <div className="rounded-lg border p-3 text-sm text-slate-500">Round 2 picks will appear here…</div>
              </>
            )}
          </div>
        </aside>
      </div>

      {/* Player Modal - new 2-column layout with sticky tabs and bigger viewport */}
      <PlayerInfoModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        player={modalPlayer}
        players={[samplePlayers[0], samplePlayers[1], samplePlayers[2], samplePlayers[3]]}
      />
    </div>
  )
}

function SuggestionRow({
  p,
  onDraft,
  disabled,
  onOpen,
}: { p: Player; onDraft: () => void; disabled?: boolean; onOpen?: (p: Player) => void }) {
  return (
    <Card className="shadow-sm">
      <CardContent className="p-3 md:p-4">
        <div className="flex items-center gap-3 md:gap-4">
          <div className="relative w-16 h-16 rounded bg-slate-200 overflow-hidden">
            <Image
              src={p.headshot || "/placeholder.svg?height=96&width=96&query=hockey%20player%20headshot"}
              alt={p.name}
              fill
              className="object-cover"
            />
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => onOpen?.(p)}
                className="text-base md:text-lg font-semibold text-left hover:underline focus:outline-none focus:underline"
              >
                {p.name}
              </button>
              <Badge variant="outline">{p.pos}</Badge>
              <span className="text-xs text-slate-500">Bye {p.bye}</span>
            </div>
            <div className="text-xs text-slate-600">
              Overall {p.overall} ({p.pos}) • ADP {p.adp}
            </div>
          </div>

          <div className="hidden md:flex flex-col items-end mr-2">
            <div className="text-emerald-600 font-semibold text-sm">{p.expertPct}%</div>
            <div className="text-[11px] text-slate-500 -mt-1">Experts</div>
          </div>

          <div className="flex items-center gap-2">
            <Button onClick={onDraft} disabled={disabled} className="min-w-[84px]">
              Draft
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function PlayerInfoModal({
  open,
  onOpenChange,
  player,
  players = [],
}: {
  open: boolean
  onOpenChange: (o: boolean) => void
  player: Player | null
  players?: Player[]
}) {
  const initial = player ?? players[0] ?? null
  const [active, setActive] = useState<Player | null>(initial)
  const [season, setSeason] = useState("2024")

  useEffect(() => {
    if (player) setActive(player)
  }, [player])

  if (!active) return null

  const isMcDavid = active.id.startsWith("mcdavid")
  const headerGradient = "from-red-700 via-red-600 to-rose-600"

  const age = isMcDavid ? 28 : 27
  const statusChip = isMcDavid
    ? { text: "HEALTHY", className: "bg-emerald-100 text-emerald-800" }
    : { text: "DAY-TO-DAY", className: "bg-yellow-100 text-yellow-800" }
  const headerSubtitle = `${active.pos} • ${active.team}  •  Bye ${active.bye}  •  Age ${age}`

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/* Widen modal by roughly 2x */}
      <DialogContent className="w-[98vw] max-w-[1800px] max-h-[96vh] p-0 overflow-hidden rounded-2xl">
        {/* Close button */}
        <DialogClose asChild>
          <button
            aria-label="Close"
            className="absolute right-3 top-3 z-20 flex h-8 w-8 items-center justify-center rounded-full bg-white/90 text-slate-700 shadow hover:bg-white"
          >
            <X className="w-4 h-4" />
          </button>
        </DialogClose>

        {/* Single-column player profile (no left picker) */}
        <section className="bg-white">
          {/* Hero Header */}
          <div className={`bg-gradient-to-r ${headerGradient} text-white`}>
            <div className="flex items-center gap-4 p-5 md:p-6">
              <div className="relative w-20 h-20 md:w-24 md:h-24 rounded-lg overflow-hidden ring-2 ring-white/30">
                <Image
                  src={active.headshot || "/placeholder.svg?height=128&width=128&query=hockey%20player%20headshot"}
                  alt={active.name}
                  fill
                  className="object-cover"
                />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className={`text-[11px] font-semibold px-2 py-0.5 rounded ${statusChip.className}`}>
                    {statusChip.text}
                  </span>
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-white/15">
                    Cross Border Eligible
                  </span>
                </div>
                <h2 className="text-3xl md:text-4xl font-extrabold leading-tight">
                  {isMcDavid ? "Connor McDavid" : active.name}
                </h2>
                <p className="text-sm md:text-[13px] text-white/85">{headerSubtitle}</p>
              </div>
              <div className="hidden md:flex items-center gap-2">
                <Button size="sm" className="bg-white text-slate-900 hover:bg-white/90">
                  Draft Now
                </Button>
                <button className="inline-flex items-center gap-1 rounded-full bg-white/15 px-3 py-1 text-xs">
                  HALF 
                </button>
              </div>
            </div>

            {/* Quick metrics */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2 px-5 pb-5 text-center">
              <Metric label="ADP" value={isMcDavid ? "1.01" : `#${active.adp}`} />
              <Metric label="ECR" value={isMcDavid ? "1" : `${active.overall}`} />
              <Metric label="Last Season" value={isMcDavid ? "153 Pts" : "—"} />
              <Metric label="SOS" value={isMcDavid ? "12th" : "—"} />
              <Metric label="Health" value={isMcDavid ? "Healthy" : "Monitor"} />
            </div>
          </div>

          {/* Scrollable body with sticky tabs */}
          <div className="max-h-[calc(96vh-220px)] overflow-auto">
            <Tabs defaultValue="news" className="w-full">
              {/* Tabs Row - pill style, sticky */}
              <div className="sticky top-0 z-10 bg-white border-b">
                <div className="flex items-center justify-between px-5 py-2">
                  <TabsList className="bg-slate-100 rounded-full p-1 flex flex-wrap gap-1">
                    {[
                      { val: "news", label: "Latest News" },
                      { val: "gamelogs", label: "Game Logs" },
                      { val: "season", label: "Season Stats" },
                      { val: "outlook", label: "Outlook" },
                      { val: "analysis", label: "News & Analysis" },
                      { val: "leagues", label: "Leagues" },
                    ].map((t) => (
                      <TabsTrigger
                        key={t.val}
                        value={t.val}
                        className="rounded-full px-3 py-1 text-sm data-[state=active]:bg-white data-[state=active]:text-blue-700 data-[state=active]:shadow-sm"
                      >
                        {t.label}
                      </TabsTrigger>
                    ))}
                  </TabsList>

                  <button className="hidden md:inline-flex items-center gap-1 text-xs text-slate-600 hover:text-slate-900">
                    Full Profile <Ellipsis className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Latest News */}
              <TabsContent value="news" className="px-5 py-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl md:text-2xl font-semibold">Consensus Draft Sentiment</h3>
                  <span className="text-[11px] text-slate-500">powered by Coach</span>
                </div>
                <p className="text-slate-700 text-[15px]">
                  {isMcDavid
                    ? "McDavid remains the premier fantasy C with unmatched scoring and playmaking. Expect elite power‑play usage and category coverage. Minor lineup tweaks in EDM shouldn't impact his top‑overall status."
                    : "Strong fantasy profile; role and PP usage will drive ceiling. Monitor preseason deployment."}
                </p>

                {/* Expert note card */}
                <div className="rounded-xl border bg-white">
                  <div className="p-5">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-full bg-slate-200 overflow-hidden" />
                      <div className="flex-1">
                        <div className="text-xs font-semibold text-slate-500">EXPERT NOTE</div>
                        <p className="text-sm text-slate-700 mt-1">
                          {isMcDavid
                            ? "McDavid's combination of elite shot volume, PP touches, and on‑ice creativity keeps his floor sky‑high. Even with regression, he's a tier of his own at the top."
                            : "Solid upside with room to grow in favorable situations. Keep an eye on linemates and PP unit."}
                        </p>
                        <div className="text-xs text-slate-500 mt-2">2 days ago</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Game Logs preview with year selector */}
                <div className="pt-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">Game Logs</h4>
                    <Select value={season} onValueChange={setSeason}>
                      <SelectTrigger className="w-28 h-8">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="2024">2024</SelectItem>
                        <SelectItem value="2023">2023</SelectItem>
                        <SelectItem value="2022">2022</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="mt-2 rounded-lg border p-4 text-sm text-slate-600">Detailed logs coming soon.</div>
                </div>
              </TabsContent>

              {/* Game Logs */}
              <TabsContent value="gamelogs" className="px-5 py-5">
                <div className="rounded-lg border p-4 bg-white text-sm text-slate-600">
                  For McDavid, expect multi‑point clusters around heavy PP usage. More detailed table coming.
                </div>
              </TabsContent>

              {/* Season Stats */}
              <TabsContent value="season" className="px-5 py-5">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <Stat title="G" value={isMcDavid ? "54" : "—"} />
                  <Stat title="A" value={isMcDavid ? "89" : "—"} />
                  <Stat title="PTS" value={isMcDavid ? "143" : "—"} />
                  <Stat title="PPP" value={isMcDavid ? "46" : "—"} />
                </div>
              </TabsContent>

              {/* Outlook */}
              <TabsContent value="outlook" className="px-5 py-5">
                <div className="rounded-lg border p-4 bg-white text-sm text-slate-700">
                  {isMcDavid
                    ? "Locked in as 1.01. If drafting early, stack an elite RW or D on the wrap. Category teams benefit from his heavy assists base."
                    : "Reliable fantasy profile with upside if role expands. Strong mid‑round target."}
                </div>
              </TabsContent>

              {/* News & Analysis */}
              <TabsContent value="analysis" className="px-5 py-5">
                <ul className="space-y-3 text-sm">
                  <li className="rounded-lg border p-3 bg-white">
                    EDM beat: "Top PP reps look crisp in camp." <span className="text-xs text-slate-500">— 1d</span>
                  </li>
                  <li className="rounded-lg border p-3 bg-white">
                    Projection note: "Top‑3 in total points." <span className="text-xs text-slate-500">— 3d</span>
                  </li>
                </ul>
              </TabsContent>

              {/* Leagues */}
              <TabsContent value="leagues" className="px-5 py-5">
                <div className="rounded-lg border p-4 bg-white text-sm text-slate-600">
                  Sync your league to tailor projections and roster fit.
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </section>
      </DialogContent>
    </Dialog>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-white/10 backdrop-blur px-3 py-2">
      <div className="text-[11px] uppercase tracking-wide opacity-80">{label}</div>
      <div className="text-base font-semibold">{value}</div>
    </div>
  )
}

function Stat({ title, value }: { title: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-slate-500">{title}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  )
}
