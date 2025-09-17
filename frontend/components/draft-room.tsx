"use client"

import { useMemo, useState, useEffect, useRef } from "react"
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
import MyTeamTab from "@/components/my-team-tab"
import CapSummaryTab from "@/components/cap-summary-tab"
import { useAuth } from "@/lib/auth-context"
import LoginModal from "@/components/login-modal"

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

export default function DraftRoom({ autoLoadUhhp = false, poolId }: { autoLoadUhhp?: boolean; poolId?: string }) {
  const { user, teamMembership } = useAuth()
  // Timer and core state are declared below; we define teams after capTeams is available
  // capTeams must be declared before teams
  const [capTeams, setCapTeams] = useState<any[] | null>(null)
  // Public mode: allow a visitor to select which team they control for writes
  const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null)
  useEffect(() => {
    try {
      const v = localStorage.getItem('uhhp_action_team_id')
      if (v) setSelectedTeamId(v)
    } catch {}
  }, [])
  useEffect(() => {
    try {
      if (selectedTeamId) localStorage.setItem('uhhp_action_team_id', selectedTeamId)
    } catch {}
  }, [selectedTeamId])
  // Resolve an actionable team_id for write actions (nominate/bid)
  const actionTeamId: string | null = useMemo(() => {
    try {
      if (selectedTeamId) return String(selectedTeamId)
      if (teamMembership?.team_id) return String(teamMembership.team_id)
      // Fallback by team name when present
      const tn = (teamMembership as any)?.team_name
      if (tn && Array.isArray(capTeams)) {
        const hit = capTeams.find((t: any) => (t?.team_name || '') === tn)
        if (hit?.team_id != null) return String(hit.team_id)
      }
      // Fallback by user email against login/attached_email
      const email = (user as any)?.email
      if (email && Array.isArray(capTeams)) {
        const hit = capTeams.find((t: any) => (t?.login === email) || (t?.attached_email === email))
        if (hit?.team_id != null) return String(hit.team_id)
      }
    } catch {}
    return null
  }, [selectedTeamId, teamMembership?.team_id, (teamMembership as any)?.team_name, (user as any)?.email, capTeams])

  // If no selection yet and teams are loaded, default to the first team
  useEffect(() => {
    if (!selectedTeamId && Array.isArray(capTeams) && capTeams.length) {
      setSelectedTeamId(String(capTeams[0].team_id))
    }
  }, [capTeams, selectedTeamId])
  // ... existing code ...

  // Real league teams from draft_state capTeams
  const teams: Team[] = useMemo(() => {
    if (Array.isArray(capTeams) && capTeams.length) {
      return capTeams.map((t: any) => ({ id: String(t.team_id), name: String(t.team_name) }))
    }
    return []
  }, [capTeams])

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
  const yourTeamId = useMemo(() => {
    // Use attached team if available
    try {
      // Lazy import auth to avoid re-ordering
    } catch {}
    // Fallback to first team
    return teams[0]?.id || ""
  }, [teams])
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
  // Draft pick nomination order (team_id list)
  const [auctionOrder, setAuctionOrder] = useState<string[]>([])
  // Separate tie-break order (independent from pick order)
  const [tieOrder, setTieOrder] = useState<string[]>([])
  const [tieAudit, setTieAudit] = useState<Array<{ pick: number; winners: string[]; advantage: string | null }>>([])

  // 3s reveal countdown when all bids submitted
  const allSubmitted = useMemo(() => teams.every((t) => gmBids[t.id] !== undefined), [teams, gmBids])
  // Do NOT auto-start reveal on load; start only when admin clicks Reveal
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
          if (winners.length > 1 && (tieOrder || []).length) {
            // Decide by whoever is higher (lower index) in current tie-break order by team_id
            let bestIdx = Infinity
            let advId: string | null = null
            for (const t of winners) {
              const tid = t.id
              const idx = tieOrder.indexOf(tid)
              if (idx >= 0 && idx < bestIdx) { bestIdx = idx; advId = tid }
            }
            if (advId) {
              finalWinnerId = advId
              // Move the winner to the bottom of the order
              setTieOrder((prev) => {
                const i = prev.indexOf(advId as string)
                if (i < 0) return prev
                const copy = [...prev]
                const [moved] = copy.splice(i, 1)
                copy.push(moved)
                return copy
              })
              // Audit log entry (by names for display)
              const idToName: Record<string, string> = {}
              teams.forEach((t) => { idToName[t.id] = t.name })
              const tiedNames = winners.map((t) => t.name)
              const advName = idToName[advId]
              setTieAudit((prev) => ([...prev, { pick: (uhhpPicks?.length || 0) + 1, winners: tiedNames, advantage: advName || null }]))
            }
          }
          if (finalWinnerId) {
            const newPick = { team: teamAbbr(teams.find((t) => t.id === finalWinnerId)?.name || ""), player: nominated.player, pos: (nominated.pos || "").toString().toUpperCase(), price: top }
            setUhhpPicks((prev) => ([...(prev || []), newPick]))
            // Also add the won player to the winner's roster in My Team (local view)
            try {
              const winnerTeamName = (nameById[finalWinnerId] || teams.find((t) => t.id === finalWinnerId)?.name || "").toString()
              setStage1Teams((prev) => {
                const copy = Array.isArray(prev) ? [...prev] : []
                for (let i = 0; i < copy.length; i++) {
                  const row: any = copy[i]
                  if ((row?.team_name || "") === winnerTeamName) {
                    const players: any[] = Array.isArray(row.players) ? [...row.players] : []
                    players.push({
                      player: nominated.player,
                      pos: (nominated.pos || "").toString().toUpperCase(),
                      salary: Number(top || 0),
                      price: Number(top || 0),
                      years: 1,
                      team: String(row?.team_id || ""),
                      nhl_player_id: (nominated as any)?.nhl_player_id ?? undefined,
                      status: (() => {
                        try {
                          const pid = (nominated as any)?.nhl_player_id
                          return pid ? (statusById[Number(pid)] || undefined) : undefined
                        } catch { return undefined }
                      })(),
                      team_abbr: (nominated as any)?.team_abbr || "",
                      birthdate: (nominated as any)?.birthdate || null,
                    })
                    copy[i] = { ...row, players }
                    break
                  }
                }
                return copy
              })
            } catch {}
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
    if (tieOrder && tieOrder.length) {
      let best: string | null = null
      let bestIdx = Infinity
      for (const id of tieTeams) {
        const idx = tieOrder.indexOf(id)
        if (idx >= 0 && idx < bestIdx) {
          bestIdx = idx
          best = id
        }
      }
      if (best) return best
    }
    return tieTeams[0] ?? null
  }, [tieTeams, tieOrder, teams])

  // Suggestions + rankings (derived from projections)
  const [suggestions, setSuggestions] = useState<Player[]>([])
  const [rankings, setRankings] = useState<Player[]>([])

  // Left rail tabs state
  const [leftTab, setLeftTab] = useState<"rankings" | "teams" | "queue">("rankings")
  const [modalOpen, setModalOpen] = useState(false)
  const [modalPlayer, setModalPlayer] = useState<Player | null>(null)
  const [showAvailable, setShowAvailable] = useState(false)
  const [posFilter, setPosFilter] = useState<"All" | "C" | "W" | "D" | "G">("All")
  const [faFilter, setFaFilter] = useState<"All" | "UFA" | "RFA">("All")
  const [bidAmount, setBidAmount] = useState<string>("")
  const [nominated, setNominated] = useState<any | null>(null)
  const [bidSubmitted, setBidSubmitted] = useState<Record<string, boolean>>({})
  const [submittedHover, setSubmittedHover] = useState<boolean>(false)
  const [currentPickNum, setCurrentPickNum] = useState<number>(1)
  const [uhhpPicks, setUhhpPicks] = useState<any[]>([])
  const [fpMap, setFpMap] = useState<Record<string, number>>({})
  const [ageMap, setAgeMap] = useState<Record<string, number>>({})
  const [projections, setProjections] = useState<any[] | null>(null)
  const [projectionSource, setProjectionSource] = useState<string>("avg")
  const [projectionSources, setProjectionSources] = useState<Array<{ slug: string; display_name: string }>>([])
  const computedProjectionSources = useMemo(() => {
    // Show Master list and VORP baselines
    return [
      { slug: 'avg', display_name: 'Master List' },
      { slug: 'vorp_available', display_name: 'VORP $100' },
      { slug: 'vorp_all', display_name: 'VORP $120' },
      { slug: 'vorp_cap', display_name: 'VORP Cap' },
    ]
  }, [])
  const [stage1Teams, setStage1Teams] = useState<any[] | null>(null)
  const [selectedTeamName, setSelectedTeamName] = useState<string | null>(null)
  const [benchSet, setBenchSet] = useState<Set<string>>(new Set())
  const [emptySlots, setEmptySlots] = useState<Set<string>>(new Set())
  const [capHits, setCapHits] = useState<number>(0)
  const [capHitsInput, setCapHitsInput] = useState<string>("0")
  const [capHitsByTeam, setCapHitsByTeam] = useState<Record<string, number>>({})
  const totalAvailableCap = useMemo(() => {
    try {
      if (!Array.isArray(stage1Teams)) return 0
      // Compute spend (years 1-3) per team from stage1Teams
      const spendByTeam: Record<string, number> = {}
      for (const t of stage1Teams) {
        const tid = String(t.team_id)
        let spend = 0
        for (const p of (t.players || [])) {
          const yrs = Number(p?.years)
          if (yrs === 1 || yrs === 2 || yrs === 3) {
            const sal = Number(p?.salary || p?.price || 0)
            if (Number.isFinite(sal)) spend += sal
          }
        }
        spendByTeam[tid] = spend
      }
      let sumAvail = 0
      for (const t of (stage1Teams || [])) {
        const tid = String(t.team_id)
        const spend = spendByTeam[tid] || 0
        const hits = capHitsByTeam[tid] || 0
        const avail = 100 - (spend + hits)
        if (avail > 0) sumAvail += avail
      }
      return sumAvail
    } catch { return 0 }
  }, [stage1Teams, capHitsByTeam])
  const [targets, setTargets] = useState<Record<string, { player: any | null; bid: string }>>({})
  const [projIdFP, setProjIdFP] = useState<Record<number, number>>({})
  const [projPosById, setProjPosById] = useState<Record<number, string>>({})
  const [projPosByName, setProjPosByName] = useState<Record<string, string>>({})
  const [vorpById, setVorpById] = useState<Record<number, number>>({})
  const [vorpSalaryById, setVorpSalaryById] = useState<Record<number, number>>({})
  // Admin tools moved to Settings modal
  const [settingsOpen, setSettingsOpen] = useState<boolean>(false)
  const [scoringRules, setScoringRules] = useState<any[] | null>(null)
  const [auctionState, setAuctionState] = useState<any | null>(null)
  const currentAuctionId = useMemo(() => (auctionState?.open_auctions?.[0]?.id ?? null), [auctionState])
  const [wsConnected, setWsConnected] = useState<boolean>(false)
  const wsRef = useRef<WebSocket | null>(null)
  const [statusById, setStatusById] = useState<Record<number, "UFA" | "RFA">>({})
  const [availableById, setAvailableById] = useState<Record<number, { status: "UFA" | "RFA"; controlling_team_id: string | null }>>({})
  const [availableSet, setAvailableSet] = useState<Set<number>>(new Set())
  const [availableReady, setAvailableReady] = useState<boolean>(false)
  const availableLoadedRef = useRef(false)
  const auctionInitRef = useRef(false)
  const [contractLockedIds, setContractLockedIds] = useState<Set<number>>(new Set())
  const [saveDirty, setSaveDirty] = useState<boolean>(false)
  const [saveLoading, setSaveLoading] = useState<boolean>(false)

  const getApiBase = () => ((process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith("http")) ? (process.env.NEXT_PUBLIC_API_BASE as string) : "http://localhost:8000")

  const auctionStateLoadingRef = useRef(false)
  const auctionStateToastedRef = useRef(false)
  const lastAuctionFetchRef = useRef<number>(0)
  async function loadAuctionState() {
    try {
      if (auctionStateLoadingRef.current) return
      const now = Date.now()
      if (now - lastAuctionFetchRef.current < 750) return
      auctionStateLoadingRef.current = true
      const apiBase = getApiBase()
      const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/auction/state`, { cache: "no-store" })
      if (!res.ok) return
      const json = await res.json()
      setAuctionState(json)
      // Seed GM bids/bidSubmitted from server top bid so reconnect shows live state
      try {
        const open = (json?.open_auctions || [])[0]
        if (open && (open.top_team_id != null) && (open.top_amount != null)) {
          const tid = String(open.top_team_id)
          const amt = Number(open.top_amount)
          setGmBids((prev) => ({ ...prev, [tid]: amt }))
          setBidSubmitted((prev) => ({ ...prev, [tid]: true }))
        }
      } catch {}
      // Only toast once on first successful load to avoid repeated messages
      if (!auctionStateToastedRef.current) {
        try { toast.success('Loaded UHHP draft state') } catch {}
        auctionStateToastedRef.current = true
      }
    } catch {}
    finally {
      auctionStateLoadingRef.current = false
      lastAuctionFetchRef.current = Date.now()
    }
  }

  async function nominatePlayerByProjection(p: Player) {
    try {
      const apiBase = getApiBase()
      const nhlId = parseInt(String(p.id), 10)
      const body: any = { nhl_player_id: Number.isFinite(nhlId) ? nhlId : undefined, team_id: actionTeamId }
      const tokensStr = (typeof window !== 'undefined') ? localStorage.getItem('kinde_tokens') : null
      let authHeader: Record<string,string> = { 'Content-Type': 'application/json' }
      try {
        const tk = tokensStr ? JSON.parse(tokensStr) : null
        const at = tk && typeof tk.access_token === 'string' ? tk.access_token : null
        if (at) authHeader = { ...authHeader, Authorization: `Bearer ${at}` }
      } catch {}
      const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/auction/nominate`, { method: 'POST', headers: authHeader, body: JSON.stringify(body) })
      if (res.ok) {
        toast.success('Nominated')
        // Optimistically set banner so the UI reflects the nomination immediately
        try {
          const pid = Number.isFinite(nhlId) ? nhlId : NaN
          const posRaw = (p.pos || '').toString().toUpperCase()
          const pos = (posRaw === 'LW' || posRaw === 'RW') ? 'W' : posRaw
          const type = Number.isFinite(pid) ? (statusById[pid] || '—') : '—'
          setNominated({ player: p.name || (p as any)?.player || '', nhl_player_id: pid, pos, type })
          // Also set current auction id immediately so bidding is enabled without waiting for state poll
          try {
            const json = await res.clone().json().catch(() => null)
            const aid = json && typeof json.auction_id === 'number' ? json.auction_id : null
            if (aid) {
              setAuctionState((prev: any) => ({
                ...(prev || {}),
                open_auctions: [{ id: aid, nhl_player_id: pid }, ...((prev && prev.open_auctions) || [])],
              }))
            }
          } catch {}
        } catch {}
        await loadAuctionState()
      } else {
        toast.error('Nomination failed')
      }
    } catch { toast.error('Nomination failed') }
  }

  async function submitBid(amount: number) {
    if (!currentAuctionId || !actionTeamId) { toast.error('No auction or team'); return }
    try {
      const apiBase = getApiBase()
      const amt = Math.max(0, Math.floor(Number(amount || 0)))
      const yourTeamKey = String(actionTeamId)
      const isRebid = !!bidSubmitted[yourTeamKey] || !!revealed
      const body: any = { auction_id: Number(currentAuctionId), team_id: yourTeamKey, amount: amt }
      if (isRebid) { body.rebid = true; if (revealed) body.tiebreak = true }
      try { console.log('[BID]', { auctionId: currentAuctionId, teamId: yourTeamKey, amt, isRebid, revealed }) } catch {}
      try { toast.message(`Submitting bid $${amt} (auction ${currentAuctionId}, team ${yourTeamKey})`) } catch {}
      const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/auction/bid`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      if (res.ok) {
        const js = await res.json().catch(() => ({} as any))
        const top = js && js.top_bid ? js.top_bid : null
        if (top && top.team_id) {
          setGmBids((prev) => ({ ...prev, [String(top.team_id)]: Number(top.amount) }))
          setBidSubmitted((prev) => ({ ...prev, [String(top.team_id)]: true }))
        } else {
          setGmBids((prev) => ({ ...prev, [yourTeamKey]: amt }))
          setBidSubmitted((prev) => ({ ...prev, [yourTeamKey]: true }))
        }
        toast.success('Bid submitted')
        await loadAuctionState()
      } else {
        const txt = await res.text().catch(() => '')
        toast.error(`Bid failed ${txt ? `– ${txt}` : ''}`)
        await loadAuctionState()
      }
    } catch { toast.error('Bid failed') }
  }

  async function matchRfa() {
    if (!currentAuctionId || !teamMembership?.team_id) { toast.error('No auction or team'); return }
    try {
      const apiBase = getApiBase()
      const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/auction/match`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ auction_id: currentAuctionId, team_id: teamMembership.team_id }) })
      if (res.ok) {
        toast.success('Matched')
        await loadAuctionState()
      } else {
        toast.error('Match failed')
      }
    } catch { toast.error('Match failed') }
  }

  // Persist the auction result server-side and refresh
  async function finalizeAuction() {
    try {
      if (!currentAuctionId) { toast.error('No auction'); return }
      const apiBase = getApiBase()
      const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/auction/finalize`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ auction_id: currentAuctionId })
      })
      if (!res.ok) { toast.error('Finalize failed'); return }
      toast.success('Auction finalized')
      // Reload state and draft data
      await loadAuctionState()
      try { await refreshCapSummary() } catch {}
      try { await loadAuctionHistory() } catch {}
      // Clear local bidding state
      setGmBids({})
      setBidSubmitted({})
      setRevealed(false)
      setNominated(null)
    } catch { toast.error('Finalize failed') }
  }

  // Connect WebSocket for event-driven updates; fall back to polling if not connected
  useEffect(() => {
    function getWsUrl() {
      const base = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith("http"))
        ? (process.env.NEXT_PUBLIC_API_BASE as string)
        : "http://localhost:8000"
      try {
        const u = new URL(base)
        u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
        u.pathname = `/ws/cbs/league/uhhp`
        u.search = ''
        return u.toString()
      } catch {
        return "ws://localhost:8000/ws/cbs/league/uhhp"
      }
    }
    let ws: WebSocket | null = null
    try {
      const url = getWsUrl()
      // Avoid multiple sockets
      if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
        return
      }
      ws = new WebSocket(url)
      wsRef.current = ws
      ws.onopen = () => { setWsConnected(true); try { loadAuctionState() } catch {} }
      ws.onclose = () => { setWsConnected(false); try { loadAuctionState() } catch {} }
      ws.onerror = () => setWsConnected(false)
      ws.onmessage = () => {
        // On any auction event, refresh state
        loadAuctionState()
      }
    } catch {
      setWsConnected(false)
    }
    return () => { try { wsRef.current?.close() } catch {} ; wsRef.current = null }
  }, [])

  // Derive/refresh the nominated banner from server state
  useEffect(() => {
    try {
      const a = auctionState?.open_auctions?.[0] || null
      if (!a) { setNominated(null); return }
      const pid = Number(a?.nhl_player_id)
      let name = ''
      let pos = ''
      if (Number.isFinite(pid)) {
        // name/pos from projections by id
        const ppos = (projPosById[pid] || '').toString().toUpperCase()
        pos = (ppos === 'LW' || ppos === 'RW') ? 'W' : (ppos || '')
        if (Array.isArray(rankings) && rankings.length) {
          const hit = rankings.find((r: any) => Number(r?.id) === pid)
          if (hit) name = String((hit as any)?.name || (hit as any)?.player || '')
        }
      }
      // fallback by name key if present in state
      if (!name) name = String(a?.player_name || a?.nhl_player_id || '')
      const type = (Number.isFinite(pid) && statusById[pid]) ? statusById[pid] : '—'
      setNominated({ player: name, nhl_player_id: Number.isFinite(pid) ? pid : undefined, pos, type })
    } catch {}
  }, [auctionState, rankings, projPosById, statusById])

  useEffect(() => {
    if (!auctionInitRef.current) {
      loadAuctionState()
      auctionInitRef.current = true
    }
    if (wsConnected) return
    const id = setInterval(loadAuctionState, 5000)
    return () => clearInterval(id)
  }, [wsConnected])

  // Admin-triggered reveal countdown (3s)
  useEffect(() => {
    function onReveal() {
      setRevealTimer((v) => (v === null ? 3 : v))
    }
    window.addEventListener('uhhp:reveal', onReveal)
    return () => window.removeEventListener('uhhp:reveal', onReveal)
  }, [])

  // Admin-triggered finalize
  useEffect(() => {
    function onFinalize() { finalizeAuction() }
    window.addEventListener('uhhp:finalize', onFinalize)
    return () => window.removeEventListener('uhhp:finalize', onFinalize)
  }, [currentAuctionId])

  // Hydrate picks list from backend auction history
  async function loadAuctionHistory(limit: number = 50) {
    try {
      const apiBase = getApiBase()
      const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/auction/history?limit=${limit}`, { cache: 'no-store' })
      if (!res.ok) return
      const js = await res.json()
      let rows: any[] = Array.isArray(js?.results) ? js.results : []
      // Sort by pick number asc (if available), otherwise by closed_at asc
      try {
        rows = [...rows].sort((a: any, b: any) => {
          const pa = (a?.pick_num != null ? Number(a.pick_num) : Number.POSITIVE_INFINITY)
          const pb = (b?.pick_num != null ? Number(b.pick_num) : Number.POSITIVE_INFINITY)
          if (pa !== pb) return pa - pb
          const da = a?.closed_at ? new Date(a.closed_at).getTime() : 0
          const db = b?.closed_at ? new Date(b.closed_at).getTime() : 0
          return da - db
        })
      } catch {}
      // Build quick lookup for player names/positions from projections
      const nameByNhlId: Record<number, string> = {}
      const posByNhlId: Record<number, string> = {}
      try {
        if (Array.isArray(rankings)) {
          for (const p of rankings) {
            const pid = Number((p as any)?.id)
            if (Number.isFinite(pid)) {
              if ((p as any)?.name) nameByNhlId[pid] = String((p as any).name)
              if ((p as any)?.pos) posByNhlId[pid] = String((p as any).pos)
            }
          }
        }
      } catch {}
      const picks = rows.map((r: any, idx: number) => {
        const tid = String((r?.winner_team_id ?? r?.team_id ?? ''))
        const nm = nameById[tid] || String(r?.winner_team_name || '')
        let playerName = String(r?.player_name || r?.name || '')
        if (!playerName) {
          try {
            const pid = Number(r?.nhl_player_id)
            if (Number.isFinite(pid) && nameByNhlId[pid]) playerName = nameByNhlId[pid]
          } catch {}
        }
        let pos = String(r?.position || r?.pos || '').toUpperCase()
        if (!pos) {
          try {
            const pid = Number(r?.nhl_player_id)
            if (Number.isFinite(pid) && posByNhlId[pid]) pos = String(posByNhlId[pid]).toUpperCase()
          } catch {}
        }
        const price = Number(r?.winning_amount ?? r?.amount ?? 0)
        const pick = (r?.pick_num != null ? Number(r.pick_num) : (idx + 1))
        const bids = Array.isArray(r?.bids) ? r.bids : []
        return { team: teamAbbr(nm), team_id: tid, player: playerName, pos, price, pick, bids, nhl_player_id: r?.nhl_player_id }
      })
      setUhhpPicks(picks)
    } catch {}
  }

  // Rehydrate picks with names/positions once projections arrive
  useEffect(() => {
    try {
      if (!Array.isArray(rankings) || !Array.isArray(uhhpPicks) || uhhpPicks.length === 0) return
      const nameByNhlId: Record<number, string> = {}
      const posByNhlId: Record<number, string> = {}
      for (const p of rankings) {
        const pid = Number((p as any)?.id)
        if (Number.isFinite(pid)) {
          if ((p as any)?.name) nameByNhlId[pid] = String((p as any).name)
          if ((p as any)?.pos) posByNhlId[pid] = String((p as any).pos)
        }
      }
      const updated = uhhpPicks.map((r: any) => {
        if (r?.player) return r
        const pid = Number((r as any)?.nhl_player_id)
        const player = Number.isFinite(pid) && nameByNhlId[pid] ? nameByNhlId[pid] : r.player
        const pos = (!r?.pos && Number.isFinite(pid) && posByNhlId[pid]) ? String(posByNhlId[pid]).toUpperCase() : r.pos
        return { ...r, player, pos }
      })
      setUhhpPicks(updated)
    } catch {}
  }, [rankings])

  // Load on initial mount/reconnect
  useEffect(() => {
    loadAuctionHistory().catch(() => {})
  }, [])

  // Load saved cap hits for this team
  useEffect(() => {
    const loadCapHits = async () => {
      try {
        if (!teamMembership?.team_id) return
        const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith('http')) ? (process.env.NEXT_PUBLIC_API_BASE as string) : 'http://localhost:8000'
        const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/cap_hits`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ team_id: String(teamMembership.team_id), cap_hits: capHits }) })
        toast.success('Cap hits saved')
      } catch { toast.error('Save failed') }
    }
    loadCapHits()
  }, [teamMembership, capHits])
  const leagueIdEnv = process.env.NEXT_PUBLIC_LEAGUE_ID || "1"
  const draftStateLoadedRef = useRef(false)
  const draftStateLoadingRef = useRef(false)
  const projLoadedRef = useRef(false)
  const triedCapFallbackRef = useRef(false)
  // Prevent stale projection responses from overwriting current selection
  const projFetchAbortRef = useRef<AbortController | null>(null)
  const projReqSeqRef = useRef(0)
  // Load all team cap hits for Cap Summary
  useEffect(() => {
    const loadAllCapHits = async () => {
      try {
        const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith('http')) ? (process.env.NEXT_PUBLIC_API_BASE as string) : 'http://localhost:8000'
        const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/cap_hits`, { method: 'GET', cache: 'no-store' })
        if (!res.ok) return
        const data = await res.json()
        const map: Record<string, number> = {}
        const arr: any[] = Array.isArray(data) ? data : (Array.isArray(data?.cap_hits) ? data.cap_hits : [])
        for (const it of arr) {
          const tid = String((it as any)?.team_id ?? '')
          const v = Number((it as any)?.cap_hits ?? 0)
          if (tid) map[tid] = Number.isFinite(v) ? v : 0
        }
        setCapHitsByTeam(map)
      } catch {}
    }
    loadAllCapHits()
  }, [])

  // Draft state provides all rosters; no extra fetches per team
  const loadRosterForMyTeam = async (_teamName: string) => { return }

  // Optional: fetch projections only if draft_state did not provide ID-based FP
  useEffect(() => {
    const fetchProjFP = async () => {
      try {
        // Cancel previous in-flight request
        if (projFetchAbortRef.current) {
          try { projFetchAbortRef.current.abort() } catch {}
        }
        const controller = new AbortController()
        projFetchAbortRef.current = controller
        const reqId = ++projReqSeqRef.current
        const srcAtStart = (projectionSource || '').trim().toLowerCase()
        const apiBase = (process.env.NEXT_PUBLIC_API_BASE && process.env.NEXT_PUBLIC_API_BASE.startsWith("http"))
          ? (process.env.NEXT_PUBLIC_API_BASE as string)
          : "http://localhost:8000"
        const src = (projectionSource || '').trim()
        const qs = new URLSearchParams({ season: String(2025), league_id: String(leagueIdEnv), limit: String(10000) })
        if (src) qs.set('source', src)
        const res = await fetch(`${apiBase}/api/projections?${qs.toString()}`, { cache: "no-store", signal: controller.signal })
        if (!res.ok) return
        const json = await res.json()
        // Combine projections if provided in separate lists (e.g., skaters/forwards and goalies)
        let arr: any[] = []
        if (Array.isArray(json?.results)) {
          arr = json.results
        } else if (Array.isArray(json)) {
          arr = json
        } else {
          const containers: any[] = [json, (json && json.data) || null, (json && json.projections) || null].filter(Boolean)
          const keys = [
            'results','players','skaters','forwards','goalies','goalie','tenders','all','list','items'
          ]
          const collected: any[] = []
          for (const c of containers) {
            for (const k of keys) {
              if (Array.isArray(c?.[k])) collected.push(...c[k])
            }
          }
          arr = collected.length ? collected : []
        }
        // Sort by fantasy points desc
        try {
          arr = [...arr].sort((a: any, b: any) => Number(b?.fantasy_points || 0) - Number(a?.fantasy_points || 0))
        } catch {}
        const mapByName: Record<string, number> = {}
        const mapById: Record<number, number> = {}
        const posById: Record<number, string> = {}
        const posByName: Record<string, string> = {}
        for (const row of arr) {
          const nm = ((row?.player_name || "").toString().trim().toLowerCase())
          const fp = typeof row?.fantasy_points === 'number' ? row.fantasy_points : undefined
          const pid = Number(row?.nhl_player_id)
          const rawPos = String(row?.position || row?.pos || '').toUpperCase()
          const primary = rawPos.split(/[\s,\/]+/)[0]
          const pos = (primary === 'LW' || primary === 'RW') ? 'W' : primary
          if (nm && fp != null) mapByName[nm] = fp
          if (pid && fp != null) mapById[pid] = fp
          if (pid) posById[pid] = pos
          if (nm) posByName[nm] = pos
        }
        // Guard against stale response
        if (projReqSeqRef.current !== reqId) return
        if ((projectionSource || '').trim().toLowerCase() !== srcAtStart) return
        if (Object.keys(mapByName).length) {
          setFpMap((prev) => ({ ...prev, ...mapByName }))
        }
        if (Object.keys(mapById).length) setProjIdFP(mapById)
        if (Object.keys(posById).length) setProjPosById(posById)
        if (Object.keys(posByName).length) setProjPosByName(posByName)
        // Build UI rankings list from projections
        const toPlayer = (r: any, idx: number): Player => ({
          id: String(r.nhl_player_id ?? r.player_name ?? idx),
          name: String(r.player_name || ''),
          team: String(r.team || r.nhl_team || r.nhl || ''),
          pos: (() => { const raw = String(r.position || r.pos || '').toUpperCase(); const p = raw.split(/[\s,\/]+/)[0]; return (p === 'LW' || p === 'RW') ? 'W' : p })(),
          bye: 0,
          overall: idx + 1,
          adp: idx + 1,
          expertPct: 0,
          headshot: undefined,
        })
        const players: Player[] = arr.map((r: any, idx: number) => toPlayer(r, idx))
        if (projReqSeqRef.current !== reqId) return
        if ((projectionSource || '').trim().toLowerCase() !== srcAtStart) return
        setRankings(players)
        setSuggestions(players.slice(0, 4))
        // Capture VORP if present (vorp_* sources), otherwise clear
        try {
          const vmap: Record<number, number> = {}
          const vsmap: Record<number, number> = {}
          for (const r of arr) {
            const pid = Number(r?.nhl_player_id)
            if (!Number.isFinite(pid)) continue
            if (typeof r?.vorp === 'number') vmap[pid] = r.vorp
            if (typeof r?.vorp_salary === 'number') vsmap[pid] = r.vorp_salary
          }
          if (projReqSeqRef.current !== reqId) return
          if ((projectionSource || '').trim().toLowerCase() !== srcAtStart) return
          setVorpById(vmap)
          setVorpSalaryById(vsmap)
        } catch {}
        // Build right panel projections list (proceeds even if available not loaded yet)
        const projItems = arr
          // If available list is present, only show those players
          .filter((r: any) => {
            const pid = Number(r?.nhl_player_id)
            if (!availableSet || availableSet.size === 0) return true
            return Number.isFinite(pid) ? availableSet.has(pid) : true
          })
          .map((r: any) => ({
          nhl_player_id: Number(r.nhl_player_id),
          player: String(r.player_name || ''),
          pos: (() => { const raw = String(r.position || r.pos || '').toUpperCase(); const p = raw.split(/[\s,\/]+/)[0]; return (p === 'LW' || p === 'RW') ? 'W' : p })(),
          team: String(r.team || r.nhl_team || r.nhl || ''),
          fp: typeof r.fantasy_points === 'number' ? r.fantasy_points : undefined,
          vorp: (typeof r?.vorp === 'number' ? r.vorp : undefined),
          vorp_salary: (typeof r?.vorp_salary === 'number' ? r.vorp_salary : undefined),
        }))
        if (projReqSeqRef.current !== reqId) return
        if ((projectionSource || '').trim().toLowerCase() !== srcAtStart) return
        setProjections(projItems)
      } catch {}
    }
    fetchProjFP()
  }, [leagueIdEnv, projectionSource, availableReady, availableSet])

  // Enrich status map using available endpoint so UFAs/RFAs appear for unrostered players
  useEffect(() => {
    if (availableLoadedRef.current) return
    const loadAvailable = async () => {
      try {
        const apiBase = (process.env.NEXT_PUBLIC_API_BASE && process.env.NEXT_PUBLIC_API_BASE.startsWith("http"))
          ? (process.env.NEXT_PUBLIC_API_BASE as string)
          : "http://localhost:8000"
        const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/auction/available?season=2025&limit=10000`, { cache: "no-store" })
        if (!res.ok) return
        const json = await res.json()
        const items = Array.isArray(json?.available) ? json.available : []
        if (!items.length) return
        setStatusById((prev) => {
          const copy = { ...prev }
          for (const it of items) {
            const pid = Number(it?.nhl_player_id)
            const st = (it?.status || '').toString().toUpperCase()
            if (Number.isFinite(pid) && (st === 'UFA' || st === 'RFA')) copy[pid] = st
          }
          return copy
        })
        setAvailableById(() => {
          const map: Record<number, { status: "UFA" | "RFA"; controlling_team_id: string | null }> = {}
          for (const it of items) {
            const pid = Number(it?.nhl_player_id)
            const st = (it?.status || '').toString().toUpperCase()
            if (Number.isFinite(pid) && (st === 'UFA' || st === 'RFA')) {
              map[pid] = { status: st as any, controlling_team_id: it?.controlling_team_id || null }
            }
          }
          return map
        })
        setAvailableSet(() => {
          const s = new Set<number>()
          for (const it of items) {
            const pid = Number(it?.nhl_player_id)
            if (Number.isFinite(pid)) s.add(pid)
          }
          return s
        })
        setAvailableReady(true)
        availableLoadedRef.current = true
      } catch {}
    }
    loadAvailable()
  }, [])

  // Load league-wide cap totals for all 12 teams (fallback only; draft_state already sets capTeams)
  useEffect(() => {
    if (draftStateLoadedRef.current) return
    if (triedCapFallbackRef.current) return
    if (Array.isArray(capTeams) && capTeams.length > 0) return
    const loadCap = async () => {
      try {
        const apiBase = (process.env.NEXT_PUBLIC_API_BASE && process.env.NEXT_PUBLIC_API_BASE.startsWith("http"))
          ? (process.env.NEXT_PUBLIC_API_BASE as string)
          : "http://localhost:8000"
        const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/teams`, { cache: "no-store" })
        if (!res.ok) return
        const json = await res.json()
        setCapTeams(Array.isArray(json?.teams) ? json.teams : [])
      } catch {}
    }
    triedCapFallbackRef.current = true
    loadCap()
  }, [leagueIdEnv, capTeams])

  // Map team_id -> team_name from CBS teams list (authoritative)
  const nameById = useMemo(() => {
    const map: Record<string, string> = {}
    for (const t of (capTeams || [])) {
      const id = String((t?.team_id ?? ''))
      const nm = (t?.team_name || '').toString()
      if (id && nm) map[id] = nm
    }
    return map
  }, [capTeams])

  // Map real team name -> logo URL from CBS league teams
  const logoByTeamName = useMemo(() => {
    const map: Record<string, string> = {}
    for (const t of (capTeams || [])) {
      const nm = (t?.team_name || "").toString().trim().toLowerCase()
      const url = (t?.logo_url || "").toString()
      if (nm && url) map[nm] = url
    }
    return map
  }, [capTeams])

  // Map team abbreviation -> logo URL (use CBS-provided abbrev when available; fallback to derived)
  const logoByAbbr = useMemo(() => {
    const map: Record<string, string> = {}
    for (const t of (capTeams || [])) {
      const url = (t?.logo_url || "").toString()
      if (!url) continue
      const abbrRaw = (t?.abbrev || "").toString().trim().toUpperCase()
      if (abbrRaw) {
        map[abbrRaw] = url
      } else {
        const derived = teamAbbr((t?.team_name || "").toString())
        if (derived) map[derived] = url
      }
    }
    return map
  }, [capTeams])

  function toggleBench(playerName: string) {
    const key = normalizeName(playerName)
    setBenchSet((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }
  const effectivePoolId = useMemo(() => (poolId || process.env.NEXT_PUBLIC_POOL_ID || "1"), [poolId])

  async function loadUhhp() {
    try {
      if (draftStateLoadedRef.current || draftStateLoadingRef.current) return
      draftStateLoadingRef.current = true
      const apiBase = (process.env.NEXT_PUBLIC_API_BASE && process.env.NEXT_PUBLIC_API_BASE.startsWith("http"))
        ? (process.env.NEXT_PUBLIC_API_BASE as string)
        : "http://localhost:8000"
      // Use consolidated draft_state endpoint
      const url = `${apiBase}/api/public/cbs/league/uhhp/draft_state`
      const res = await fetch(url, { cache: "no-store" })
      if (!res.ok) throw new Error("draft_state failed")
      const data = await res.json()
      // Cap Summary teams (merge in attached_email/login from /teams)
      const teamsArr = Array.isArray(data?.teams) ? data.teams : []
      try {
        const teamsRes = await fetch(`${apiBase}/api/public/cbs/league/uhhp/teams`, { cache: 'no-store' })
        if (teamsRes.ok) {
          const tdata = await teamsRes.json()
          const enrich: Record<string, any> = {}
          for (const t of (Array.isArray(tdata?.teams) ? tdata.teams : [])) {
            const tid = String((t?.team_id ?? ''))
            if (tid) enrich[tid] = t
          }
          const merged = teamsArr.map((t: any) => {
            const tid = String((t?.team_id ?? ''))
            const more = enrich[tid]
            return more ? { ...t, attached_email: more.attached_email, login: more.login, is_admin: more.is_admin } : t
          })
          setCapTeams(merged)
        } else {
          setCapTeams(teamsArr)
        }
      } catch {
        setCapTeams(teamsArr)
      }
      setScoringRules(Array.isArray(data?.scoring_rules) ? data.scoring_rules : [])
      setProjectionSources(Array.isArray(data?.projection_sources) ? data.projection_sources : [])
      // Always hydrate auction order directly from cbs_auction_order
      try {
        const apiBase = (process.env.NEXT_PUBLIC_API_BASE && process.env.NEXT_PUBLIC_API_BASE.startsWith("http"))
          ? (process.env.NEXT_PUBLIC_API_BASE as string)
          : "http://localhost:8000"
        const ordRes = await fetch(`${apiBase}/api/public/cbs/league/uhhp/auction/order`, { cache: 'no-store' })
        let orderIds: string[] = []
        if (ordRes.ok) {
          const ord = await ordRes.json()
          const arr: Array<{ pos: number; team_id: string }> = Array.isArray(ord?.order) ? ord.order : []
          if (arr.length) orderIds = arr.sort((a,b)=>Number(a.pos)-Number(b.pos)).map((o) => String(o.team_id))
        }
        if (orderIds.length === 0 && teamsArr.length) {
          orderIds = teamsArr.map((t: any) => String(t?.team_id || '')).filter(Boolean)
        }
        if (orderIds.length) {
          if (!auctionOrder.length) setAuctionOrder(orderIds)
          if (!(tieOrder && tieOrder.length)) setTieOrder(orderIds)
        }
      } catch {}
      // Build stage1Teams from roster payload for My Team
      const rosters = Array.isArray(data?.rosters) ? data.rosters as any[] : []
      const byTeam: Record<string, any[]> = {}
      const nextStatus: Record<number, "UFA" | "RFA"> = {}
      const locked = new Set<number>()
      for (const r of rosters) {
        const t = String(r.team_id)
        if (!byTeam[t]) byTeam[t] = []
        const salaryNum = r?.salary ? Number(r.salary) : 0
        // Skip non-player cap-hit placeholders
        const nameNorm = (r?.player_name || "").toString().trim().toLowerCase()
        if (nameNorm.startsWith("z-caphit") || nameNorm.includes("draft pick")) {
          continue
        }
        if (typeof r?.nhl_player_id === 'number') {
          const st = (r?.status || '').toString().toUpperCase()
          if (st === 'UFA' || st === 'RFA') nextStatus[Number(r.nhl_player_id)] = st
          const yrs = Number(r?.years)
          if (yrs === 1 || yrs === 2) locked.add(Number(r.nhl_player_id))
        }
        byTeam[t].push({
          player: (r?.player_name || String(r?.cbs_player_id) || String(r?.nhl_player_id)),
          pos: ((r?.position || "").toString().toUpperCase()),
          salary: salaryNum,
          price: salaryNum,
          years: r?.years,
          team: String(r?.team_id),
          nhl_player_id: (typeof r?.nhl_player_id === 'number' ? r.nhl_player_id : undefined),
          status: r?.status,
          team_abbr: (r as any)?.nhl_team_abbr || '',
          birthdate: (r as any)?.birthdate || null,
        })
      }
      setStatusById(nextStatus)
      setContractLockedIds(locked)
      const stageTeams = (Array.isArray(data?.teams) ? data.teams as any[] : []).map((t) => ({
        team_id: t.team_id,
        team_name: t.team_name,
        players: byTeam[String(t.team_id)] || [],
      }))
      setStage1Teams(stageTeams)
      // Default selected
      const prefer = stageTeams.find((t: any) => (t?.team_name || "") === "New Oilers Nation")
      setSelectedTeamName(prefer ? String(prefer.team_name) : (stageTeams[0]?.team_name || "New Oilers Nation"))
      // Build projection FP map by nhl id
      const projMap: Record<number, number> = {}
      for (const r of rosters) {
        if (typeof r?.nhl_player_id === 'number' && typeof r?.fantasy_points === 'number') {
          projMap[Number(r.nhl_player_id)] = Number(r.fantasy_points)
        }
      }
      setProjIdFP(projMap)
      draftStateLoadedRef.current = true
      toast.success("Loaded UHHP draft state")
    } catch (e) {
      toast.error("Failed to load UHHP state")
    } finally {
      draftStateLoadingRef.current = false
    }
  }

  // Refresh Cap Summary data on-demand (cap hits + latest rosters/teams)
  async function refreshCapSummary() {
    try {
      const apiBase = (process.env.NEXT_PUBLIC_API_BASE && process.env.NEXT_PUBLIC_API_BASE.startsWith("http"))
        ? (process.env.NEXT_PUBLIC_API_BASE as string)
        : "http://localhost:8000"
      // Fetch cap hits and draft_state in parallel
      const [capRes, dsRes, teamsRes] = await Promise.all([
        fetch(`${apiBase}/api/public/cbs/league/uhhp/cap_hits`, { method: 'GET', cache: 'no-store' }),
        fetch(`${apiBase}/api/public/cbs/league/uhhp/draft_state`, { cache: 'no-store' }),
        fetch(`${apiBase}/api/public/cbs/league/uhhp/teams`, { cache: 'no-store' }),
      ])
      if (capRes.ok) {
        const data = await capRes.json()
        const map: Record<string, number> = {}
        const arr: any[] = Array.isArray(data) ? data : (Array.isArray(data?.cap_hits) ? data.cap_hits : [])
        for (const it of arr) {
          const tid = String((it as any)?.team_id ?? '')
          const v = Number((it as any)?.cap_hits ?? 0)
          if (tid) map[tid] = Number.isFinite(v) ? v : 0
        }
        setCapHitsByTeam(map)
      }
      if (dsRes.ok) {
        const data = await dsRes.json()
        const teamsArr = Array.isArray(data?.teams) ? data.teams : []
        if (teamsRes.ok) {
          try {
            const tdata = await teamsRes.json()
            const enrich: Record<string, any> = {}
            for (const t of (Array.isArray(tdata?.teams) ? tdata.teams : [])) {
              const tid = String((t?.team_id ?? ''))
              if (tid) enrich[tid] = t
            }
            const merged = teamsArr.map((t: any) => {
              const tid = String((t?.team_id ?? ''))
              const more = enrich[tid]
              return more ? { ...t, attached_email: more.attached_email, login: more.login, is_admin: more.is_admin } : t
            })
            setCapTeams(merged)
          } catch { setCapTeams(teamsArr) }
        } else {
          setCapTeams(teamsArr)
        }
        const rosters = Array.isArray(data?.rosters) ? data.rosters as any[] : []
        const byTeam: Record<string, any[]> = {}
        for (const r of rosters) {
          const t = String(r.team_id)
          if (!byTeam[t]) byTeam[t] = []
          const salaryNum = r?.salary ? Number(r.salary) : 0
          const nameNorm = (r?.player_name || "").toString().trim().toLowerCase()
          if (nameNorm.startsWith("z-caphit") || nameNorm.includes("draft pick")) continue
          byTeam[t].push({
            player: (r?.player_name || String(r?.cbs_player_id) || String(r?.nhl_player_id)),
            pos: ((r?.position || "").toString().toUpperCase()),
            salary: salaryNum,
            price: salaryNum,
            years: r?.years,
            future_fa: (r as any)?.future_fa,
            team: String(r?.team_id),
            nhl_player_id: (typeof r?.nhl_player_id === 'number' ? r.nhl_player_id : undefined),
            status: (r as any)?.status,
            type: (r as any)?.status,
            team_abbr: (r as any)?.nhl_team_abbr || '',
            birthdate: (r as any)?.birthdate || null,
          })
        }
        const stageTeams = (Array.isArray(data?.teams) ? data.teams as any[] : []).map((t) => ({
          team_id: t.team_id,
          team_name: t.team_name,
          players: byTeam[String(t.team_id)] || [],
        }))
        setStage1Teams(stageTeams)
      }
    } catch {}
  }

  // When switching viewed team, load that team's local roster layout and cap hit
  useEffect(() => {
    try {
      if (!selectedTeamName || !Array.isArray(stage1Teams)) return
      const team = (stage1Teams || []).find((t: any) => (t?.team_name || '') === selectedTeamName)
      const tid = team && team.team_id ? String(team.team_id) : ''
      if (!tid) return
      // Load saved layout for this team
      const key = `uhhp_layout_${tid}`
      const raw = localStorage.getItem(key)
      let loadedLocalCap = false
      if (raw) {
        try {
          const data = JSON.parse(raw)
          if (Array.isArray(data.bench)) setBenchSet(new Set<string>(data.bench))
          if (Array.isArray(data.empty)) setEmptySlots(new Set<string>(data.empty))
          if (data.targets && typeof data.targets === 'object') setTargets(data.targets)
          if (typeof data.capHits === 'number') {
            setCapHits(data.capHits)
            setCapHitsInput(String(data.capHits))
            loadedLocalCap = true
          }
        } catch {}
      }
      // Apply cap hits from server snapshot map if available
      const serverCap = capHitsByTeam[tid]
      if (!loadedLocalCap && serverCap != null && Number.isFinite(Number(serverCap))) {
        setCapHits(Number(serverCap))
        setCapHitsInput(String(serverCap))
      }
    } catch {}
  }, [selectedTeamName, stage1Teams, capHitsByTeam])

  const uhhpTop50 = useMemo(() => (uhhpPicks.length ? uhhpPicks.slice(0, 50) : null), [uhhpPicks])
  // Compute client-side VORP salary using Cap Summary
  const clientVorpSalaryById = useMemo(() => {
    try {
      if (!Array.isArray(rankings) || rankings.length === 0) return {}
      // Build available pool for ranking view
      const pool: Array<{ id: number; vorp: number }> = []
      for (const pl of rankings) {
        const pid = Number(pl?.id)
        if (!Number.isFinite(pid)) continue
        const v = vorpById[pid]
        if (typeof v === 'number' && v > 0) pool.push({ id: pid, vorp: v })
      }
      // Market size based on roster requirements as if no players were signed
      const numTeams = Array.isArray(stage1Teams) ? stage1Teams.length : 12
      const rosterSize = 15 // 2C,3W,4D,2G,4F → 15 total
      const openSlots = Math.max(1, numTeams * rosterSize)
      pool.sort((a, b) => b.vorp - a.vorp)
      const market = pool.slice(0, openSlots)
      const sumVorp = market.reduce((s, x) => s + (x.vorp > 0 ? x.vorp : 0), 0)
      // Assume fresh budgets: $120 per team, no spend/cap hits
      const totalCap = numTeams * 120
      if (sumVorp <= 0 || totalCap <= 0) return {}
      // Price = totalCap * (vorp / sumVorp), clamped 2..30
      const out: Record<number, number> = {}
      for (const x of market) {
        const raw = totalCap * (x.vorp / sumVorp)
        const clamped = Math.max(2, Math.min(30, Math.round(raw)))
        out[x.id] = clamped
      }
      return out
    } catch {
      return {}
    }
  }, [rankings, vorpById, stage1Teams])
  const uhhpFilled50 = useMemo(() => {
    // Build 50 slots; associate each slot's team from auctionOrder
    const list: Array<{ kind: "taken" | "pending" | "nominated"; data?: any; team?: string }> = []
    const total = 50
    const takenCount = Math.min(uhhpPicks.length, total)
    for (let i = 0; i < takenCount; i++) {
      const taken = uhhpPicks[i]
      const team = taken?.team_id || (auctionOrder.length ? auctionOrder[i % auctionOrder.length] : undefined)
      list.push({ kind: "taken", data: taken, team })
    }
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

  // Keep the highlighted pick in sync with the current draft progress
  useEffect(() => {
    try {
      const taken = Array.isArray(uhhpPicks) ? uhhpPicks.length : 0
      const idx = Math.max(1, Math.min(50, taken + 1))
      setCurrentPickNum(idx)
    } catch {}
  }, [uhhpPicks, nominated])

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
    if (!autoLoadUhhp) return
    // Only load once
    if (draftStateLoadedRef.current) return
      loadUhhp()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoLoadUhhp])

  // Listen for pick order updates from settings modal
  useEffect(() => {
    function onSetPickOrder(e: any) {
      try {
        const incoming = Array.isArray(e?.detail?.order) ? e.detail.order : []
        if (!incoming.length) return
        // Accept either ids or names; convert names to ids if needed
        const haveIds = incoming.every((x) => teams.some((t) => t.id === String(x)))
        if (haveIds) {
          const ids = incoming.map((x) => String(x))
          setAuctionOrder(ids)
          setTieOrder(ids)
        } else {
          const nameToId: Record<string, string> = {}
          teams.forEach((t) => { nameToId[t.name] = t.id })
          const ids = incoming.map((n) => nameToId[String(n)]).filter(Boolean)
          if (ids.length) { setAuctionOrder(ids); setTieOrder(ids) }
        }
      } catch {}
    }
    window.addEventListener('uhhp:set-pick-order', onSetPickOrder as any)
    return () => window.removeEventListener('uhhp:set-pick-order', onSetPickOrder as any)
  }, [])

  // Persist and restore My Team layout: bench, empty slots, targets, cap hits
  useEffect(() => {
    try {
      const key = `uhhp_layout_${teamMembership?.team_id || 'anon'}`
      const raw = localStorage.getItem(key)
      if (!raw) return
      const data = JSON.parse(raw)
      if (Array.isArray(data.bench)) setBenchSet(new Set<string>(data.bench))
      if (Array.isArray(data.empty)) setEmptySlots(new Set<string>(data.empty))
      if (data.targets && typeof data.targets === 'object') setTargets(data.targets)
      if (typeof data.capHits === 'number') { setCapHits(data.capHits); setCapHitsInput(String(data.capHits)) }
      setSaveDirty(false)
    } catch {}
  }, [teamMembership?.team_id])
  const markDirty = () => setSaveDirty(true)
  const saveLayout = async () => {
    try {
      setSaveLoading(true)
      const key = `uhhp_layout_${teamMembership?.team_id || 'anon'}`
      const payload = {
        bench: Array.from(benchSet),
        empty: Array.from(emptySlots),
        targets,
        capHits,
      }
      localStorage.setItem(key, JSON.stringify(payload))
      // Also persist cap hits to backend
      try {
        const tid = actionTeamId
        if (tid) {
          const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith('http')) ? (process.env.NEXT_PUBLIC_API_BASE as string) : 'http://localhost:8000'
          await fetch(`${apiBase}/api/public/cbs/league/uhhp/cap_hits`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ team_id: String(tid), cap_hits: capHits }) })
        }
      } catch {}
      toast.success('Layout saved')
      setSaveDirty(false)
    } catch {
      toast.error('Save failed')
    } finally {
      setSaveLoading(false)
    }
  }

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
            <button className="p-2 hover:bg-slate-800 rounded" onClick={() => setSettingsOpen(true)}>
              <Settings className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 max-w-xl mx-6">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-300">Controlling team</span>
              <select
                className="h-8 bg-slate-800 border border-slate-700 text-white text-sm rounded px-2"
                value={selectedTeamId || ''}
                onChange={(e) => setSelectedTeamId(e.target.value || null)}
              >
                {(Array.isArray(capTeams) ? capTeams : []).map((t: any) => (
                  <option key={String(t.team_id)} value={String(t.team_id)}>{String(t.team_name)}</option>
                ))}
              </select>
            </div>
          </div>

          <DraftTopbarAuth />
        </div>
      </div>

      {/* Main content columns */}
      <div className="w-full grid grid-cols-1 md:grid-cols-[280px_minmax(0,1fr)_340px] gap-4 px-0 py-4 h-full items-stretch">
        {/* Left: Rankings rail with tabs */}
        <aside className="rounded-none border-r bg-white h-full flex flex-col min-h-0">
          {/* Tabs header (Auction | Tie Break) */}
          <div className="p-3 border-b">
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
              <div className="ml-auto" />
            </div>
          </div>

          {/* Removed section header spacer */}

          {/* Pick Order block removed per request */}

          {/* Admin controls removed from left rail */}

          {/* Content area */}
          <div className="h-[calc(100vh-56px-32px)] overflow-auto p-3">
            {leftTab === "rankings" && (
              <>
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
                                          id: r.nhl_player_id || r.player,
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
                                        {r.player || `#${r.pick || (idx + 1)}`}
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
                                        <div className="text-[12px] text-slate-600 break-words">{nameById[String(entry.team || "")] || nameById[String(r.team_id || "")] || ""}</div>
                                        {r.pick ? (
                                          <div className="text-[12px] text-slate-500">Pick {r.pick}</div>
                                        ) : null}
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
                                  <div className="text-[12px] text-slate-600 break-words">{nameById[String(entry.team || "")] || ""}</div>
                                </div>
                              </>
                            ) : (
                              <>
                                <div className="text-[12px] text-slate-600 break-words">{nameById[String(entry.team || "")] || ""}</div>
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
                          <div className="text-[12px] text-slate-600 break-words">{p.team}</div>
                        </div>
                      </div>

                      {/* FP display from projections */}
                      <div className="text-right text-[13px] font-bold text-rose-600 pr-1">
                        {(() => {
                          const key = (p.name || '').toString().trim().toLowerCase()
                          const fp = fpMap[key]
                          return typeof fp === 'number' ? fp.toFixed(1) : '—'
                        })()}
                      </div>
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
                          className={cn("ml-1", (!currentAuctionId) ? "opacity-50 text-slate-400 cursor-not-allowed" : undefined)}
                          disabled={!currentAuctionId}
                          onClick={() => {
                            if (!currentAuctionId) { toast.message("No open auction"); return }
                            if (revealed && !tieTeams.includes(yourTeamId)) return
                            setBidAmount("0")
                            submitBid(0)
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
                      className="w-12 h-8 pl-4 text-center bg-white"
                      value={bidAmount}
                      onChange={(e) => {
                        const raw = e.target.value
                        const cleaned = raw.replace(/[^0-9]/g, "")
                        setBidAmount(cleaned)
                      }}
                      onBlur={() => {
                        if (bidAmount === "") return
                        const n = Math.floor(Number(bidAmount))
                        if (Number.isFinite(n)) {
                          setBidAmount(String(Math.max(2, n)))
                        }
                      }}
                      placeholder=""
                    />
                  </div>
                  {(() => {
                    const isSubmitted = !!bidSubmitted[yourTeamId]
                    const youInTie = revealed && tieTeams.includes(yourTeamId)
                    const disabled = !currentAuctionId
                    const label = (isSubmitted && !revealed) ? "Cancel" : (youInTie ? "Re-Bid" : "Submit Bid")
                    const baseCls = "ml-2"
                    const stateCls = youInTie
                      ? "bg-orange-500 hover:bg-orange-600 text-white"
                      : (isSubmitted && !revealed)
                            ? "bg-rose-600 hover:bg-rose-700 text-white"
                        : undefined
                    return (
                      <Button
                        className={cn(baseCls, stateCls, disabled ? "opacity-50 cursor-not-allowed" : undefined)}
                        disabled={disabled}
                        onClick={() => {
                          if (!currentAuctionId) return
                          const isSub = !!bidSubmitted[yourTeamId]
                          if (isSub && !revealed) {
                            setBidSubmitted((prev) => ({ ...prev, [yourTeamId]: false }))
                            setGmBids((prev) => { const cp = { ...prev }; delete cp[yourTeamId]; return cp })
                            toast.message("Bid cancelled")
                            return
                          }
                          const amt = Math.floor(Number(bidAmount || "0"))
                          submitBid(amt)
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
                <div className="text-xs text-slate-500 mb-1">GM Bids {revealed ? "(revealed)" : (revealTimer !== null ? `(revealing in ${revealTimer}s)` : "(hidden until all submit)")}</div>
                <div className="flex items-center gap-3 overflow-x-auto whitespace-nowrap py-1">
                  {teams.map((t) => {
                    const submitted = !!bidSubmitted[t.id]
                    const bid = gmBids[t.id]
                    const isTie = revealed && tieTeams.includes(t.id)
                    const hasAdv = revealed && tieAdvantageTeamId === t.id && isTie
                    const displayName = nameById[t.id] || t.name
                    const normName = (displayName || "").toString().trim().toLowerCase()
                    const logoUrl = logoByTeamName[normName] || logoByAbbr[teamAbbr(displayName)]
                    return (
                      <div key={t.id} className="inline-flex items-center flex-col">
                        {logoUrl ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={logoUrl}
                            alt={displayName}
                            title={displayName}
                            className={cn(
                              "w-12 h-12 rounded-full object-cover border border-slate-200",
                              hasAdv ? "ring-2 ring-orange-700" : undefined,
                            )}
                          />
                        ) : (
                        <div
                          className={cn(
                            "w-12 h-12 rounded-full flex items-center justify-center text-[12px] font-bold",
                            submitted && !revealed ? "bg-emerald-500 text-white" : "bg-slate-200 text-slate-700",
                            isTie ? "bg-orange-400 text-white" : undefined,
                            hasAdv ? "ring-2 ring-orange-700" : undefined,
                          )}
                            title={displayName}
                        >
                            {teamAbbr(displayName)}
                        </div>
                        )}
                        {!revealed && (
                          <div className="mt-1 h-[14px] text-[11px] text-slate-500">{submitted ? "●" : "–"}</div>
                        )}
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
            <Tabs defaultValue="myteam" onValueChange={(v)=>{ if(v==='cap'){ refreshCapSummary() } }}>
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
                              // Render actual bids ledger when available
                              const cellBid = Array.isArray(r?.bids)
                                ? r.bids.find((b: any) => String(b?.team_id || '') === String(t.id))
                                : undefined
                              const bidVal = cellBid ? Number(cellBid.amount) : undefined
                              return (
                                <td key={t.id} className="px-2 py-2 text-right tabular-nums text-slate-600">{bidVal != null ? `$${bidVal}` : "—"}</td>
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
                  const myTeamInfo = (() => {
                    try {
                      const list = Array.isArray(capTeams) ? capTeams : []
                      return list.find((t: any) => (t?.team_name || '') === myTeamName) || null
                    } catch { return null }
                  })()
                  const myTeamEmail = (myTeamInfo as any)?.attached_email || null
                  const youAbbr = teamAbbr(myTeamName)
                  const stage1Roster = (() => {
                    const t = (stage1Teams || []).find((tt: any) => (tt?.team_name || "") === myTeamName)
                    const players: any[] = (t?.players as any[]) || []
                    return players
                  })()
                  const wonPlayers = (uhhpPicks || []).filter((r: any) => teamAbbr(r.team || "") === youAbbr && r.player)
                  const myPicks = wonPlayers.length ? wonPlayers : stage1Roster.map((p: any) => ({
                    player: p?.player || p?.player_name || p?.player_full_name || p?.display_name,
                    pos: p?.pos || p?.position,
                    price: p?.salary || 0,
                    years: p?.years,
                    future_fa: p?.future_fa,
                    team: myTeamName,
                    nhl_player_id: p?.nhl_player_id,
                    status: p?.status || p?.type,
                    type: p?.status || p?.type,
                    team_abbr: p?.team_abbr || p?.nhl_team_abbr || '',
                    birthdate: p?.birthdate || null,
                  }))
                  const byPos: Record<string, any[]> = { C: [], W: [], F: [], D: [], G: [] }
                  const reserves: any[] = []
                  const normalizeRosterPos = (p: any): 'C'|'W'|'D'|'G'|'F' => {
                    const raw = (p || '').toString().trim().toUpperCase()
                    if (raw === 'LW' || raw === 'RW') return 'W'
                    if (raw === 'D' || raw === 'DEF' || raw === 'DEFENSE' || raw === 'DEFENCE') return 'D'
                    if (raw === 'C' || raw === 'CTR' || raw === 'CENTER' || raw === 'CENTRE') return 'C'
                    if (raw === 'G' || raw === 'GK' || raw === 'GL' || raw === 'GOALIE' || raw === 'GOALTENDER') return 'G'
                    if (raw === 'W') return 'W'
                    if (raw === 'FWD' || raw === 'F') return 'F'
                    return (byPos[raw] ? (raw as any) : 'F')
                  }
                  const resolveRosterPos = (rec: any): 'C'|'W'|'D'|'G'|'F' => {
                    // Prefer explicit/normalized roster pos if clearly typed
                    const norm = normalizeRosterPos(rec?.pos)
                    if (norm === 'C' || norm === 'W' || norm === 'D' || norm === 'G') return norm
                    // Fallback: use projections by id or name
                    try {
                      const pid = Number((rec as any)?.nhl_player_id)
                      if (Number.isFinite(pid) && projPosById[pid]) {
                        const ppos = (projPosById[pid] || '').toString().toUpperCase()
                        if (ppos === 'C' || ppos === 'W' || ppos === 'D' || ppos === 'G') return ppos as any
                      }
                      const key = normalizeName((rec?.player || rec?.player_name || rec?.player_full_name || rec?.display_name || '').toString())
                      if (key && projPosByName[key]) {
                        const ppos = (projPosByName[key] || '').toString().toUpperCase()
                        if (ppos === 'C' || ppos === 'W' || ppos === 'D' || ppos === 'G') return ppos as any
                      }
                    } catch {}
                    // If explicit roster pos is missing/ambiguous, infer from listable positions for forwards
                    return 'F'
                  }
                  for (const r of myPicks) {
                    const nameKey = normalizeName(r.player)
                    if (benchSet.has(nameKey)) {
                      reserves.push(r)
                      continue
                    }
                    const posRaw = resolveRosterPos(r)
                    const key = posRaw
                    byPos[key].push(r)
                  }
                  const getStatusFor = (rec: any) => {
                    const pid = Number((rec as any)?.nhl_player_id)
                    const mapped = Number.isFinite(pid) ? statusById[pid] : undefined
                    if (mapped === 'UFA' || mapped === 'RFA') return mapped
                    const raw = ((rec as any).status || (rec as any).type || (rec as any).fa_type || (rec as any).future_fa || "").toString().toUpperCase()
                    return raw === 'UFA' || raw === 'RFA' ? raw : '—'
                  }
                  const adjustedPrice = (rec: any) => {
                    const st = getStatusFor(rec)
                    const yrs = Number((rec as any)?.years)
                    // If player has a signed contract (1-3 years), always show real salary
                    if (yrs === 1 || yrs === 2 || yrs === 3) {
                      const s = Number((rec as any)?.price)
                      return Number.isFinite(s) ? s : 0
                    }
                    if (st === 'RFA') return 0
                    const val = Number((rec as any)?.price)
                    return Number.isFinite(val) ? val : 0
                  }
                  function take(pos: string, slotId: string) {
                    if (emptySlots.has(slotId)) return null
                    // For flexible forward slot 'F', allow W first, then C, then any F
                    if (pos === "F") {
                      return byPos.W.shift() || byPos.C.shift() || byPos.F.shift() || null
                    }
                    return byPos[pos].shift() || null
                  }
                  // Compute totals for header metrics
                  const byPosForTotals: Record<string, any[]> = {
                    C: [...byPos.C],
                    W: [...byPos.W],
                    F: [...byPos.F],
                    D: [...byPos.D],
                    G: [...byPos.G],
                  }
                  function takeForTotals(pos: string, slotId: string) {
                    if (emptySlots.has(slotId)) return null
                    if (pos === "F") {
                      return byPosForTotals.W.shift() || byPosForTotals.C.shift() || byPosForTotals.F.shift() || null
                    }
                    return (byPosForTotals[pos] || []).shift() || null
                  }
                  let totalSalary = 0
                  let budgetBids = 0
                  for (const row of REQUIRED_ROWS) {
                    for (let i = 0; i < row.count; i++) {
                      const slotId = `${row.label}-${i}`
                      const sim = takeForTotals(row.label, slotId)
                      if (sim) {
                        totalSalary += adjustedPrice(sim)
                      } else {
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
                    totalSalary += adjustedPrice(r)
                  }
                  const totalBudgeted = totalSalary + budgetBids
                  return (
                    <>
                      <div className="mb-3 flex items-center justify-between gap-6">
                        <div className="flex items-center gap-3">
                          <Button size="sm" variant="outline" disabled={!saveDirty || saveLoading} onClick={saveLayout}>
                            {saveLoading ? 'Saving...' : 'Save'}
                          </Button>
                          {/* Team selector to view another team's My Team roster */}
                          <select
                            className="h-8 px-2 rounded border border-slate-300 bg-white text-slate-800"
                            value={myTeamName || ''}
                            onChange={(e) => {
                              const nextName = e.target.value
                              try {
                                // Find team by name from stage1Teams and update selection name
                                const t = (stage1Teams || []).find((tt: any) => (tt?.team_name || '') === nextName)
                                if (t && t.team_id) {
                                  setSelectedTeamName(String(nextName))
                                }
                              } catch {}
                            }}
                          >
                            <option value="">Select team…</option>
                            {Array.isArray(stage1Teams) && stage1Teams.map((t: any) => (
                              <option key={String(t.team_id)} value={String(t.team_name || '')}>{String(t.team_name || t.team_id)}</option>
                            ))}
                          </select>
                        </div>
                        <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-slate-500">Cap Hits:</span>
                          <div className="relative">
                            <span className="absolute left-1.5 top-1/2 -translate-y-1/2 text-xs text-slate-500">$</span>
                            <Input
                              inputMode="numeric"
                              pattern="[0-9]*"
                              className="h-8 w-[84px] pl-4 text-center"
                              value={capHitsInput}
                              onChange={(e) => {
                                const v = (e.target.value || '').replace(/[^0-9]/g, '')
                                setCapHitsInput(v)
                                setCapHits(Number(v || 0))
                                markDirty()
                              }}
                            />
                          </div>
                        </div>
                        <div className="text-sm">
                          <span className="text-slate-500">Salary: </span>
                          <span className="font-semibold tabular-nums">{`$${totalSalary}`}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-slate-500">Total: </span>
                          <span className="font-semibold tabular-nums">{`$${totalSalary + capHits}`}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-slate-500">Budgeted: </span>
                          <span className="font-semibold tabular-nums">{`$${totalBudgeted + capHits}`}</span>
                        </div>
                        </div>
                      </div>
                      <div className="rounded-lg border">
                        <div className="grid grid-cols-[60px_minmax(0,1fr)_70px_100px_100px_100px_110px] items-stretch border-b bg-slate-50 text-xs font-semibold text-slate-600">
                          <div className="px-3 py-2">Pos</div>
                          <div className="px-3 py-2">Player</div>
                          <div className="px-3 py-2 text-center">Status</div>
                          <div className="px-3 py-2 text-center">Pro FTPS</div>
                          <div className="px-3 py-2 text-center">Contract</div>
                          <div className="px-3 py-2 text-center">VORP</div>
                          <div className="px-3 py-2 text-center">Salary</div>
                        </div>
                        <div>
                          {REQUIRED_ROWS.flatMap((row) =>
                            Array.from({ length: row.count }, (_, i) => (
                              <div key={`${row.label}-${i}`} className="grid grid-cols-[60px_minmax(0,1fr)_70px_100px_100px_100px_110px] items-center border-b">
                                <div className="px-3 py-2 text-xs font-semibold text-slate-600">{row.label}</div>
                                {(() => {
                                  const slotId = `${row.label}-${i}`
                                  const pl = take(row.label, slotId)
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
                                          const pid = Number(p?.nhl_player_id)
                                          const vorpPrice = Number.isFinite(pid) ? clientVorpSalaryById[pid] : undefined
                                          const price = (typeof vorpPrice === 'number' && vorpPrice > 0)
                                            ? vorpPrice
                                            : Math.max(2, Math.min(30, Math.round((fpv || 0) / 18)))
                                          return { p, fp: fpv, price }
                                        })
                                      const pool = budget > 0 ? withPrices.filter((x) => x.price <= budget) : withPrices
                                      if (!pool.length) return
                                      const best = pool.sort((a, b) => (b.fp - a.fp))[0]
                                      setTargets((prev) => ({
                                        ...prev,
                                        [slotId]: {
                                          player: best.p,
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
                                        <div className="px-3 py-2 text-sm text-center">—</div>
                                        <div className="px-3 py-2 text-sm tabular-nums text-center">{fp}</div>
                                        <div className="px-3 py-2 text-sm text-slate-400 text-center">—</div>
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
                                  const price = adjustedPrice(pl)
                                  const contractStr = (() => {
                                    const years = pl.years || pl.contractYears
                                    const fa = pl.future_fa
                                    if (years) return `${years}y`
                                    if (fa) return String(fa)
                                    return "—"
                                  })()
                                  const fpKey = (playerName || "").toString().trim().toLowerCase()
                                  let fpVal = undefined as number | undefined
                                  // Prefer ID-based FP when available
                                  if (typeof pl?.nhl_player_id === 'number' && projIdFP[Number(pl.nhl_player_id)] != null) {
                                    fpVal = projIdFP[Number(pl.nhl_player_id)]
                                  }
                                  if (fpVal == null && typeof fpMap[fpKey] === "number") {
                                    fpVal = fpMap[fpKey]
                                  }
                                  if (fpVal == null) {
                                    const proj = (projections || []).find((p: any) => ((p.player || "").toString().trim().toLowerCase()) === fpKey)
                                    if (proj && typeof (proj as any).fp === "number") {
                                      fpVal = (proj as any).fp
                                    }
                                  }
                                  const fpStr = fpVal != null ? fpVal.toFixed(1) : "—"
                                  const statusStr = (() => {
                                    const raw = ((pl as any).status || "").toString().toUpperCase()
                                    if (raw === 'UFA' || raw === 'RFA') return raw
                                    const pid = Number((pl as any)?.nhl_player_id)
                                    const mapped = Number.isFinite(pid) ? statusById[pid] : undefined
                                    return (mapped === 'UFA' || mapped === 'RFA') ? mapped : '—'
                                  })()
                                  const posDisp = resolveRosterPos(pl)
                                  const abbr = (pl as any)?.team_abbr ? String((pl as any).team_abbr).toUpperCase() : ''
                                  const ageStr = (() => {
                                    const bd = (pl as any)?.birthdate
                                    if (!bd) return ''
                                    try {
                                      const [y, m, d] = String(bd).split('-').map((x: string) => parseInt(x, 10))
                                      if (!y || !m || !d) return ''
                                      const cutoff = new Date(2025, 6, 1)
                                      const bdate = new Date(y, m - 1, d)
                                      let age = cutoff.getFullYear() - bdate.getFullYear()
                                      const md = (cutoff.getMonth() + 1) * 100 + cutoff.getDate()
                                      const bdmd = m * 100 + d
                                      if (md < bdmd) age -= 1
                                      return `Age: ${age}`
                                    } catch { return '' }
                                  })()
                                  const posMeta = [posDisp, abbr, ageStr].filter(Boolean).join(' · ')
                                  return (
                                    <>
                                      <div className="px-3 py-2">
                                        <div className="flex items-center gap-2 min-w-0">
                                          <div className="font-medium text-sm truncate">{playerName}</div>
                                          <button
                                            className="h-6 px-2 text-[11px] rounded border hover:bg-slate-50"
                                            onClick={() => { toggleBench(playerName); setEmptySlots((prev)=>{ const s=new Set(prev); s.add(slotId); return s }); markDirty() }}
                                            title="Move to Reserves"
                                          >
                                            Sit
                  </button>
                                          <span className="ml-2 text-xs text-slate-500">{posMeta}</span>
                                        </div>
                                      </div>
                                      <div className="px-3 py-2 text-sm text-center">{statusStr}</div>
                                      <div className="px-3 py-2 text-sm tabular-nums text-center">{fpStr}</div>
                                      <div className="px-3 py-2 text-sm text-center">{contractStr}</div>
                                      {(() => {
                                        const pid = Number((pl as any)?.nhl_player_id)
                                        const vRaw = Number.isFinite(pid) ? (clientVorpSalaryById[pid] ?? (vorpSalaryById as any)?.[pid]) : undefined
                                        const vPrice = (typeof vRaw === 'number' && Number.isFinite(vRaw) && vRaw > 0) ? Math.round(vRaw) : null
                                        return (
                                          <div className="px-3 py-2 text-sm font-semibold tabular-nums text-center">{vPrice != null ? `$${vPrice}` : '—'}</div>
                                        )
                                      })()}
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
                                <div className="grid grid-cols-[60px_minmax(0,1fr)_70px_100px_100px_100px_110px] items-center">
                                  <div className="px-3 py-2 text-xs font-semibold text-slate-600">Res</div>
                                  <div className="px-3 py-2 text-sm text-slate-400">None</div>
                                  <div className="px-3 py-2" />
                                  <div className="px-3 py-2" />
                                  <div className="px-3 py-2" />
                                  <div className="px-3 py-2" />
                                  <div className="px-3 py-2" />
                                </div>
                              )
                            }
                            return reserves.map((r, i) => {
                              const playerName = r.player
                              const price = adjustedPrice(r)
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
                                const raw = ((r as any).status || "").toString().toUpperCase()
                                if (raw === 'UFA' || raw === 'RFA') return raw
                                const pid = Number((r as any)?.nhl_player_id)
                                const mapped = Number.isFinite(pid) ? statusById[pid] : undefined
                                return (mapped === 'UFA' || mapped === 'RFA') ? mapped : '—'
                              })()
                              const posDisp = resolveRosterPos(r)
                              const abbr = (r as any)?.team_abbr ? String((r as any).team_abbr).toUpperCase() : ''
                              const ageStr = (() => {
                                const bd = (r as any)?.birthdate
                                if (!bd) return ''
                                try {
                                  const [y, m, d] = String(bd).split('-').map((x: string) => parseInt(x, 10))
                                  if (!y || !m || !d) return ''
                                  const cutoff = new Date(2025, 6, 1)
                                  const bdate = new Date(y, m - 1, d)
                                  let age = cutoff.getFullYear() - bdate.getFullYear()
                                  const md = (cutoff.getMonth() + 1) * 100 + cutoff.getDate()
                                  const bdmd = m * 100 + d
                                  if (md < bdmd) age -= 1
                                  return `Age: ${age}`
                                } catch { return '' }
                              })()
                              const posMeta = [posDisp, abbr, ageStr].filter(Boolean).join(' · ')
                              const hasOpenFor = (p: string) => {
                                const pref = resolveRosterPos({ pos: p, player: r.player, nhl_player_id: r.nhl_player_id })
                                const anySlot = (prefix: string) => Array.from(emptySlots).some((id) => id.startsWith(prefix + '-'))
                                if (pref === 'C' || pref === 'W') return anySlot(pref) || anySlot('F')
                                return anySlot(pref)
                              }
                              return (
                                <div key={i} className="grid grid-cols-[60px_minmax(0,1fr)_70px_100px_100px_100px_110px] items-center border-b">
                                  <div className="px-3 py-2 text-xs font-semibold text-slate-600">Res</div>
                                  <div className="px-3 py-2">
                                    <div className="flex items-center gap-2 min-w-0">
                                      <button
                                        disabled={!hasOpenFor(r.pos || '')}
                                        className="h-6 px-2 text-[11px] rounded border hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                        onClick={() => {
                                          toggleBench(playerName)
                                          // Free one suitable empty slot so this player can be placed
                                          setEmptySlots((prev) => {
                                            const next = new Set(prev)
                                            const p = resolveRosterPos(r)
                                            const tryRemove = (prefix: string) => {
                                              for (const id of Array.from(next)) {
                                                if (id.startsWith(prefix + "-")) { next.delete(id); return true }
                                              }
                                              return false
                                            }
                                            // Prefer exact position first
                                            if (!tryRemove(p)) {
                                              // For C/W also try freeing an F slot
                                              if (p === 'C' || p === 'W') tryRemove('F')
                                            }
                                            return next
                                          })
                                          markDirty()
                                        }}
                                        title="Dress (move to active)"
                                      >
                                        Dress
                  </button>
                                      <div className="font-medium text-sm truncate">{playerName}</div>
                                      <span className="ml-2 text-xs text-slate-500">{posMeta}</span>
                </div>
              </div>
                                  <div className="px-3 py-2 text-sm text-center">{statusStr}</div>
                                  <div className="px-3 py-2 text-sm tabular-nums text-center">{fpStr}</div>
                                  <div className="px-3 py-2 text-sm text-center">{contractStr}</div>
                                  {(() => {
                                    const pid = Number((r as any)?.nhl_player_id)
                                    const vRaw = Number.isFinite(pid) ? (clientVorpSalaryById[pid] ?? (vorpSalaryById as any)?.[pid]) : undefined
                                    const vPrice = (typeof vRaw === 'number' && Number.isFinite(vRaw) && vRaw > 0) ? Math.round(vRaw) : null
                                    return (
                                      <div className="px-3 py-2 text-sm font-semibold tabular-nums text-center">{vPrice != null ? `$${vPrice}` : '—'}</div>
                                    )
                                  })()}
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
                  const list = (() => {
                    const base = Array.isArray(capTeams) ? capTeams : []
                    const logoById: Record<string, string | null> = {}
                    for (const t of base) {
                      const id = String((t as any)?.team_id ?? '')
                      if (id) logoById[id] = (t as any)?.logo_url ?? null
                    }
                    if (!Array.isArray(stage1Teams) || !stage1Teams.length) return base
                    const rows: any[] = []
                    for (const t of stage1Teams) {
                      const teamId = String((t as any)?.team_id ?? '')
                      const teamName = (t as any)?.team_name
                      const players: any[] = Array.isArray((t as any)?.players) ? (t as any).players : []
                      let total = 0
                      let count = players.length
                      let rfaCount = 0
                      for (const r of players) {
                        const pid = Number((r as any)?.nhl_player_id)
                        const mapped = Number.isFinite(pid) ? statusById[pid] : undefined
                        const raw = ((r as any)?.status || (r as any)?.type || '').toString().toUpperCase()
                        const status = (mapped === 'UFA' || mapped === 'RFA') ? mapped : (raw === 'UFA' || raw === 'RFA' ? raw : undefined)
                        const yrs = Number((r as any)?.years)
                        if (status === 'RFA' && (yrs === 0 || Number.isNaN(yrs))) {
                          rfaCount += 1
                        }
                        // Use same salary logic as My Team row rendering
                        let price = 0
                        if (yrs === 1 || yrs === 2 || yrs === 3) {
                          const s = Number((r as any)?.salary ?? (r as any)?.price ?? 0)
                          price = Number.isFinite(s) ? s : 0
                        } else if (status === 'RFA') {
                          price = 0
                        } else {
                          const s = Number((r as any)?.salary ?? (r as any)?.price ?? 0)
                          price = Number.isFinite(s) ? s : 0
                        }
                        total += price
                      }
                      const capHitVal = capHitsByTeam[teamId] ?? 0
                      rows.push({
                        team_id: teamId,
                        team_name: teamName,
                        total_players: count,
                        total_salary: total,
                        rfas: rfaCount,
                        cap_hits: capHitVal,
                        logo_url: logoById[teamId] ?? null,
                      })
                    }
                    return rows
                        })()
                        return (
                    <div className="rounded border">
                      <div className="grid grid-cols-[minmax(0,1fr)_100px_120px_110px_140px] items-center bg-slate-50 border-b text-xs font-semibold text-slate-600">
                        <div className="px-3 py-2">Team</div>
                        <div className="px-3 py-2 text-right">RFA</div>
                        <div className="px-3 py-2 text-right">Cap Hits</div>
                        <div className="px-3 py-2 text-right">Free Space</div>
                        <div className="px-3 py-2 text-right">Total Salary</div>
                            </div>
                      <div>
                        {(list.length ? list : Array.from({ length: 12 }).map((_,i)=>({ team_id:`ph-${i}`, team_name:"", rfas:null, cap_hits:null, total_salary:null, logo_url:null }))).map((t: any, i: number) => (
                          <div key={t.team_id || i} className="grid grid-cols-[minmax(0,1fr)_100px_120px_110px_140px] items-center border-b">
                            <div className="px-3 py-2 flex items-center gap-2">
                              {t.logo_url ? (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img src={t.logo_url} alt={t.team_name} className="h-5 w-5 rounded object-cover" />
                              ) : (
                                <div className="h-5 w-5 rounded bg-gray-200" />
                              )}
                              <div className="truncate">{t.team_name || <span className="h-3 w-32 bg-gray-200 rounded inline-block" />}</div>
                            </div>
                            <div className="px-3 py-2 text-right text-sm tabular-nums">{t.rfas != null ? `${t.rfas}` : <span className="inline-block h-3 w-8 bg-gray-200 rounded" />}</div>
                            <div className="px-3 py-2 text-right text-sm tabular-nums">{t.cap_hits != null ? `$${Number(t.cap_hits || 0).toLocaleString()}` : <span className="inline-block h-3 w-12 bg-gray-200 rounded" />}</div>
                            <div className="px-3 py-2 text-right text-sm tabular-nums">{(t.total_salary != null || t.cap_hits != null) ? `$${Math.max(0, (100 - (Number(t.total_salary || 0) + Number(t.cap_hits || 0)))).toLocaleString()}` : <span className="inline-block h-3 w-12 bg-gray-200 rounded" />}</div>
                            <div className="px-3 py-2 text-right text-sm font-medium tabular-nums">{t.total_salary != null ? `$${Number((Number(t.total_salary || 0) + Number(t.cap_hits || 0)) || 0).toLocaleString()}` : <span className="inline-block h-3 w-16 bg-gray-200 rounded" />}</div>
                            </div>
                        ))}
                            </div>
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
                {Array.isArray(projections) && projections.length > 0 ? (
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
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {(["C","W","D","G"] as const).map((pos) => (
                      <div key={`empty-${pos}`} className="rounded-lg border bg-white">
                        <div className="px-3 py-2 border-b font-semibold text-slate-700">{pos}</div>
                        <ol className="max-h-[60vh] overflow-auto divide-y">
                          {Array.from({ length: 12 }).map((_, i) => (
                            <li key={`empty-${pos}-${i}`} className="px-3 py-1.5 flex items-center gap-2">
                              <span className="w-6 text-right text-slate-300">{i + 1}.</span>
                              <span className="flex-1 h-3 bg-gray-200 rounded" />
                              <span className="w-8 h-3 bg-gray-200 rounded" />
                            </li>
                          ))}
                        </ol>
                      </div>
                    ))}
                  </div>
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
                    <SelectValue placeholder="Select source" />
                  </SelectTrigger>
                  <SelectContent>
                    {(computedProjectionSources || []).map((s) => (
                      <SelectItem key={s.slug} value={s.slug}>{s.display_name || s.slug}</SelectItem>
                    ))}
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
                      .filter((p) => {
                        if (faFilter === "All") return true
                        const pid = Number((p as any)?.nhl_player_id)
                        const st = Number.isFinite(pid) ? (availableById[pid]?.status || statusById[pid]) : undefined
                        return (st || "").toString().toUpperCase() === faFilter
                      })
                      .filter((p) => (showAvailable ? !takenSet.has(((p.player || "").toString().trim().toLowerCase())) : true))
                      .filter((p) => {
                        const pid = Number((p as any)?.nhl_player_id)
                        return !(Number.isFinite(pid) && contractLockedIds.has(pid))
                      })
                      .map((p, i) => (
                  <div key={i} className="rounded-lg border p-3">
                    <div className="text-[11px] text-slate-500">
                      {(() => {
                        const key = (p.player || "").toString().trim().toLowerCase()
                        const pid = Number((p as any)?.nhl_player_id)
                        const faStr = (() => {
                          if (Number.isFinite(pid) && availableById[pid]?.status) return availableById[pid].status.toUpperCase()
                          if (Number.isFinite(pid) && statusById[pid]) return String(statusById[pid]).toUpperCase()
                          return (p.type || "").toString().toUpperCase() || "—"
                        })()
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
                          // Prefer VORP-calibrated price when available
                          const pid = Number((p as any)?.nhl_player_id)
                          const vorpCalced = Number.isFinite(pid) ? (clientVorpSalaryById[pid] ?? (vorpSalaryById as any)?.[pid]) : undefined
                          const projPrice = (typeof vorpCalced === 'number' && vorpCalced > 0)
                            ? Math.round(vorpCalced)
                            : (typeof fp === 'number' ? Math.max(2, Math.min(22, Math.round(fp / 20))) : null)
                          const priceStr = projPrice !== null ? `$${projPrice}` : "$—"
                          const showPrice = (projectionSource || '').toLowerCase() !== 'avg'
                          return (
                            <div className="flex flex-col items-end mr-1 leading-tight">
                              <div className="text-sm font-semibold text-slate-700">{fpStr}</div>
                              {showPrice ? (
                              <div className="text-sm font-semibold text-slate-700">{priceStr}</div>
                              ) : null}
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
                            <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 transition-colors hover:bg-blue-600 hover:text-white"
                                onClick={() => nominatePlayerByProjection({ ...p, id: String((p as any).nhl_player_id || p.player || p.name || '') } as any)}
                              >
                                Nominate
                            </Button>
                              {/* Quick Bid removed per requirements */}
                            </div>
                          )
                        })()}
                      </div>
                    </div>
                  </div>
                      ))
                  )
                })()}
              </div>
            ) : null}
          </div>
        </aside>
      </div>

      {/* Player Modal - new 2-column layout with sticky tabs and bigger viewport */}
      <PlayerInfoModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        player={modalPlayer}
        players={rankings}
      />

      <LeagueSettingsModal
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        teams={Array.isArray(capTeams) ? capTeams : []}
        scoringRules={Array.isArray(scoringRules) ? scoringRules : []}
        onRefreshCaps={refreshCapSummary}
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

function LeagueSettingsModal({
  open,
  onOpenChange,
  teams,
  scoringRules,
  onRefreshCaps,
}: {
  open: boolean
  onOpenChange: (o: boolean) => void
  teams: Array<{ team_id: string; team_name: string; owner_id?: string | null; owner_name?: string | null }>
  scoringRules: any[]
  onRefreshCaps: () => Promise<void>
}) {
  const [tab, setTab] = useState<'teams' | 'scoring' | 'history' | 'caps'>('teams')
  const [history, setHistory] = useState<any[]>([])
  const [teamsLocal, setTeamsLocal] = useState<any[]>([])
  const [knownUsers, setKnownUsers] = useState<Array<{ email: string; subject: string; display_name?: string }>>([])
  useEffect(() => {
    try {
      // Seed login with existing login or attached email (so Save persists it)
      setTeamsLocal(Array.isArray(teams)
        ? teams.map((t: any) => {
            const hasLogin = typeof t?.login === 'string' && t.login.trim().length > 0
            return { ...t, login: hasLogin ? t.login : (t?.attached_email || t?.login || null) }
          })
        : [])
    } catch { setTeamsLocal([]) }
  }, [teams, open])

  // Load saved GM credentials (login, is_admin) when modal opens on Teams tab
  useEffect(() => {
    let ignore = false
    async function loadCreds() {
      if (!open || tab !== 'teams') return
      try {
        const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith('http')) ? (process.env.NEXT_PUBLIC_API_BASE as string) : 'http://localhost:8000'
        const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/gm_credentials`)
        if (!res.ok) return
        const data = await res.json()
        const creds = Array.isArray(data?.credentials) ? data.credentials : []
        const byId: Record<string, any> = {}
        for (const c of creds) {
          if (c && c.team_id != null) byId[String(c.team_id)] = c
        }
        if (ignore) return
        setTeamsLocal((prev: any[]) => (prev || []).map((row: any) => {
          const cid = String(row?.team_id)
          const c = byId[cid]
          if (!c) return row
          const credLogin = (typeof c.login === 'string' && c.login.trim().length > 0) ? c.login : null
          return { ...row, login: credLogin ?? row.login, is_admin: !!c.is_admin }
        }))
        // Also fetch known users for assignment picker
        try {
          const usersRes = await fetch(`${apiBase}/api/public/cbs/league/uhhp/admin/users`)
          if (usersRes.ok) {
            const udata = await usersRes.json()
            const arr = Array.isArray(udata?.users) ? udata.users : []
            setKnownUsers(arr)
          }
        } catch {}
      } catch {}
    }
    loadCreds()
    return () => { ignore = true }
  }, [open, tab])

  // Hydrate cap hits when opening the Cap Hits tab
  useEffect(() => {
    let ignore = false
    async function loadCaps() {
      if (!open || tab !== 'caps') return
      try {
        const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith('http')) ? (process.env.NEXT_PUBLIC_API_BASE as string) : 'http://localhost:8000'
        const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/cap_hits`, { cache: 'no-store' })
        if (!res.ok) return
        const data = await res.json()
        const arr: any[] = Array.isArray(data) ? data : (Array.isArray(data?.cap_hits) ? data.cap_hits : [])
        const byId: Record<string, number> = {}
        for (const it of arr) {
          const tid = String((it as any)?.team_id ?? '')
          const v = Number((it as any)?.cap_hits ?? 0)
          if (tid) byId[tid] = Number.isFinite(v) ? v : 0
        }
        if (ignore) return
        setTeamsLocal((prev) => (prev || []).map((row: any) => {
          const tid = String(row?.team_id ?? '')
          return tid ? { ...row, cap_hits: byId[tid] ?? row.cap_hits } : row
        }))
      } catch {}
    }
    loadCaps()
    return () => { ignore = true }
  }, [open, tab])
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[98vw] sm:max-w-none w-[2200px] max-h-[85vh] overflow-auto" style={{ maxWidth: '98vw', width: '2200px' }}>
        <div className="flex items-center justify-between">
          <div className="text-lg font-semibold">League Settings</div>
        </div>
        <div className="mt-3">
          <div className="flex items-center gap-2 border-b">
            {(["teams","scoring","history","caps"] as const).map((t) => (
              <button key={t} onClick={() => setTab(t)} className={cn("px-3 py-2 text-sm",
                tab===t ? "border-b-2 border-blue-600 text-blue-700 font-semibold" : "text-slate-600 hover:bg-slate-50")}>{t === 'teams' ? 'Teams & GMs' : t==='scoring' ? 'Scoring' : t==='caps' ? 'Cap Hits' : 'Bid History'}</button>
            ))}
          </div>
          
          {tab === 'teams' && (
            <div className="mt-3 rounded border">
              <div className="grid grid-cols-[minmax(0,1fr)_220px_280px_240px_110px_140px] gap-3 items-center bg-slate-50 border-b text-xs font-semibold text-slate-600">
                <div className="px-3 py-2">Team (drag to reorder = Pick Order)</div>
                <div className="px-3 py-2">Assign</div>
                <div className="px-3 py-2">Login</div>
                <div className="px-3 py-2">Password</div>
                <div className="px-3 py-2">Admin</div>
                <div className="px-3 py-2 text-right">Action</div>
              </div>
              <div>
                {(teamsLocal || []).map((t: any, i: number) => (
                  <div
                    key={`${t.team_id}-${i}`}
                    className="grid grid-cols-[minmax(0,1fr)_220px_280px_240px_110px_140px] gap-3 items-center border-b"
                    draggable
                    onDragStart={(e) => { e.dataTransfer.setData('text/plain', String(i)) }}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault()
                      try {
                        const from = parseInt(e.dataTransfer.getData('text/plain') || '-1', 10)
                        const to = i
                        if (Number.isFinite(from) && from >= 0 && from < (teamsLocal || []).length && to !== from) {
                          const copy = [...(teamsLocal || [])]
                          const [moved] = copy.splice(from, 1)
                          copy.splice(to, 0, moved)
                          setTeamsLocal(copy)
                        }
                      } catch {}
                    }}
                    title="Drag to reorder pick order"
                  >
                    <div className="px-3 py-2 cursor-move">{t.team_name}</div>
                    {/* Assign */}
                    <div className="px-3 py-2">
                      <select
                        className="h-8 px-2 border rounded text-sm bg-white w-[220px]"
                        value={''}
                        onChange={async (e) => {
                          const sel = e.target.value
                          if (!sel) return
                          const [email, subject] = sel.split('|')
                          try {
                            const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith('http')) ? (process.env.NEXT_PUBLIC_API_BASE as string) : 'http://localhost:8000'
                            const body: any = { email, team_id: String(t.team_id), role: 'owner' }
                            if (subject) body.subject = subject
                            const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/admin/attach`, {
                              method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
                            })
                            if (res.ok) {
                              setTeamsLocal((prev) => prev.map((row, idx) => idx===i ? { ...row, attached_email: email, login: email } : row))
                              alert('User attached to team')
                            } else {
                              alert('Failed to attach user')
                            }
                          } catch { alert('Failed to attach user') }
                        }}
                      >
                        <option value="">Assign existing user…</option>
                        {knownUsers.map((u, idx2) => (
                          <option key={`${u.email}-${idx2}`} value={`${u.email}|${u.subject}`}>{u.display_name ? `${u.display_name} — ` : ''}{u.email}</option>
                        ))}
                      </select>
                    </div>
                    {/* Login */}
                    <div className="px-3 py-2">
                      <input
                        className="w-full h-8 px-2 border rounded text-sm"
                        placeholder="email or username"
                        value={t.login || t.attached_email || ''}
                        onChange={(e) => {
                          const v = e.target.value
                          setTeamsLocal((prev) => prev.map((row, idx) => idx===i ? { ...row, login: v } : row))
                        }}
                      />
                    </div>
                    <div className="px-3 py-2">
                      <input
                        className="w-full h-8 px-2 border rounded text-sm"
                        placeholder="set password"
                        type="password"
                        value={t._pwd || ''}
                        onChange={(e) => {
                          const v = e.target.value
                          setTeamsLocal((prev) => prev.map((row, idx) => idx===i ? { ...row, _pwd: v } : row))
                        }}
                      />
                    </div>
                    <div className="px-3 py-2">
                      <input
                        type="checkbox"
                        className="h-4 w-4"
                        checked={!!t.is_admin}
                        onChange={(e) => setTeamsLocal((prev) => prev.map((row, idx) => idx===i ? { ...row, is_admin: e.target.checked } : row))}
                      />
                    </div>
                    <div className="px-3 py-2 text-right">
                      <Button size="sm" variant="outline" onClick={() => {
                        const url = '/callback'
                        try { navigator.clipboard?.writeText(window.location.origin + url) } catch {}
                        alert(`Send this link to invite the GM to login: ${window.location.origin + url}`)
                      }}>Invite</Button>
                    </div>
                  </div>
                ))}
                {(!teamsLocal || teamsLocal.length === 0) && (
                  Array.from({ length: 12 }).map((_, i) => (
                    <div key={`ph-${i}`} className="grid grid-cols-[minmax(0,1fr)_120px] items-center border-b">
                      <div className="px-3 py-2"><div className="h-3 w-40 bg-gray-200 rounded" /></div>
                      <div className="px-3 py-2 text-right"><div className="h-7 w-16 bg-gray-200 rounded" /></div>
                    </div>
                  ))
                )}
              </div>
              <div className="flex items-center justify-end gap-2 p-2">
                <Button size="sm" variant="secondary" onClick={async () => {
                  // Persist GM credentials
                  try {
                    const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith('http')) ? (process.env.NEXT_PUBLIC_API_BASE as string) : 'http://localhost:8000'
                    const creds = (teamsLocal || []).map((x: any) => ({
                      team_id: String(x?.team_id),
                      login: (x?.login || null),
                      password: (x?._pwd || ''),
                      is_admin: !!x?.is_admin,
                    }))
                    await fetch(`${apiBase}/api/public/cbs/league/uhhp/gm_credentials`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ creds }) })
                    alert('GM credentials saved')
                  } catch {}
                }}>Save GM Settings</Button>
                <Button size="sm" onClick={async () => {
                  try {
                    const orderNames = (teamsLocal || []).map((x: any) => (x?.team_name || '').toString()).filter(Boolean)
                    window.dispatchEvent(new CustomEvent('uhhp:set-pick-order', { detail: { order: orderNames } }))
                    // Persist to backend using team_id list
                    const ids = (teamsLocal || []).map((x: any) => String(x?.team_id)).filter(Boolean)
                    const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith('http')) ? (process.env.NEXT_PUBLIC_API_BASE as string) : 'http://localhost:8000'
                    await fetch(`${apiBase}/api/public/cbs/league/uhhp/auction/order`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ order: ids }) })
                    alert('Pick order saved')
                  } catch {}
                }}>Save Order</Button>
              </div>
            </div>
          )}
          {tab === 'scoring' && (
            <div className="mt-3">
              <div className="rounded border overflow-auto max-h-64">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-50 text-slate-600">
                    <tr>
                      <th className="text-left px-3 py-2">Stat</th>
                      <th className="text-left px-3 py-2">Code</th>
                      <th className="text-right px-3 py-2">Weight</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(scoringRules || []).map((r: any, i: number) => (
                      <tr key={`sr-${i}`} className="border-t">
                        <td className="px-3 py-2">{r?.name || '—'}</td>
                        <td className="px-3 py-2">{r?.code || '—'}</td>
                        <td className="px-3 py-2 text-right tabular-nums">{Number(r?.w || 0).toFixed(2)}</td>
                      </tr>
                    ))}
                    {(!scoringRules || scoringRules.length === 0) && (
                      <tr><td className="px-3 py-2 text-slate-500" colSpan={3}>No scoring rules loaded.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          {tab === 'history' && (
            <div className="mt-3">
              <div className="mb-2 flex items-center gap-2">
                <Button size="sm" variant="outline" onClick={async () => {
                  try {
                    const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith('http')) ? (process.env.NEXT_PUBLIC_API_BASE as string) : 'http://localhost:8000'
                    const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/auction/history?limit=50`)
                    const data = await res.json()
                    setHistory(Array.isArray(data?.results) ? data.results : [])
                  } catch {}
                }}>Refresh</Button>
              </div>
              <div className="rounded border overflow-auto max-h-80">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-50 text-slate-600">
                    <tr>
                      <th className="text-left px-3 py-2">Closed At</th>
                      <th className="text-left px-3 py-2">Winner</th>
                      <th className="text-right px-3 py-2">Winning Bid</th>
                      <th className="text-right px-3 py-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(history || []).map((h: any, i: number) => (
                      <tr key={`h-${i}`} className="border-t">
                        <td className="px-3 py-2">{h.closed_at || '—'}</td>
                        <td className="px-3 py-2">{h.winner_team_id || '—'}</td>
                        <td className="px-3 py-2 text-right tabular-nums">{h.winning_amount != null ? `$${Number(h.winning_amount)}` : '—'}</td>
                        <td className="px-3 py-2 text-right">
                          <div className="flex items-center gap-2 justify-end">
                            <Button size="sm" variant="outline" onClick={async () => {
                              const pid = prompt('Enter new NHL player id to set for this nomination:')
                              if (!pid) return
                              try {
                                const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith('http')) ? (process.env.NEXT_PUBLIC_API_BASE as string) : 'http://localhost:8000'
                                await fetch(`${apiBase}/api/public/cbs/league/uhhp/auction/admin/change_nomination`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ auction_id: h.id, nhl_player_id: Number(pid) }) })
                                alert('Nomination updated')
                              } catch {}
                            }}>Change Nomination</Button>
                            <Button size="sm" variant="outline" onClick={async () => {
                              const amt = prompt('Enter new winning bid $ amount:')
                              if (!amt) return
                              try {
                                const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith('http')) ? (process.env.NEXT_PUBLIC_API_BASE as string) : 'http://localhost:8000'
                                await fetch(`${apiBase}/api/public/cbs/league/uhhp/auction/admin/update_salary`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ auction_id: h.id, amount: Number(amt) }) })
                                alert('Winning bid updated')
                              } catch {}
                            }}>Change Winning Bid</Button>
                            <Button size="sm" variant="destructive" onClick={async () => {
                              if (!confirm('Reset this nomination? This will undo the win.')) return
                              try {
                                const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith('http')) ? (process.env.NEXT_PUBLIC_API_BASE as string) : 'http://localhost:8000'
                                await fetch(`${apiBase}/api/public/cbs/league/uhhp/auction/admin/reset`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ auction_id: h.id }) })
                                alert('Nomination reset')
                              } catch {}
                            }}>Reset Nomination</Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {(!history || history.length === 0) && (
                      <tr><td className="px-3 py-6 text-slate-500" colSpan={4}>No history yet.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          {tab === 'caps' && (
            <div className="mt-3">
              <div className="rounded border overflow-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-50 text-slate-600">
                    <tr>
                      <th className="text-left px-3 py-2">Team</th>
                      <th className="text-right px-3 py-2">Cap Hits ($)</th>
                      <th className="text-right px-3 py-2">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(teamsLocal || []).map((t: any, i: number) => (
                      <tr key={`cap-${t.team_id}`} className="border-t">
                        <td className="px-3 py-2">{t.team_name}</td>
                        <td className="px-3 py-2 text-right">
                          <input
                            className="h-8 w-28 px-2 border rounded text-right"
                            inputMode="numeric"
                            pattern="[0-9]*"
                            value={String(t._cap_hits ?? t.cap_hits ?? '')}
                            onChange={(e) => {
                              const v = (e.target.value || '').replace(/[^0-9]/g, '')
                              setTeamsLocal((prev) => prev.map((row, idx) => idx===i ? { ...row, _cap_hits: v } : row))
                            }}
                          />
                        </td>
                        <td className="px-3 py-2 text-right">
                          <Button size="sm" variant="outline" onClick={async () => {
                            try {
                              const apiBase = (process.env.NEXT_PUBLIC_API_BASE && (process.env.NEXT_PUBLIC_API_BASE as string).startsWith('http')) ? (process.env.NEXT_PUBLIC_API_BASE as string) : 'http://localhost:8000'
                              const val = Number((teamsLocal[i]?._cap_hits ?? teamsLocal[i]?.cap_hits ?? 0) || 0)
                              await fetch(`${apiBase}/api/public/cbs/league/uhhp/cap_hits`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ team_id: String(t.team_id), cap_hits: val }) })
                              setTeamsLocal((prev) => prev.map((row, idx) => idx===i ? { ...row, cap_hits: val, _cap_hits: undefined } : row))
                              try { await onRefreshCaps() } catch {}
                            } catch { alert('Save failed') }
                          }}>Save</Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
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

function DraftTopbarAuth() {
  const { user, teamMembership, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const [impersonate, setImpersonate] = useState<string>("")
  const [teamsForImpersonate, setTeamsForImpersonate] = useState<Array<{ team_id: string; team_name: string }>>([])
  useEffect(() => {
    async function loadTeams() {
      try {
        const apiBase = (process.env.NEXT_PUBLIC_API_BASE && process.env.NEXT_PUBLIC_API_BASE.startsWith("http")) ? (process.env.NEXT_PUBLIC_API_BASE as string) : "http://localhost:8000"
        const res = await fetch(`${apiBase}/api/public/cbs/league/uhhp/teams`, { cache: 'no-store' })
        if (!res.ok) return
        const data = await res.json()
        const arr = Array.isArray(data?.teams) ? data.teams : []
        setTeamsForImpersonate(arr.map((t: any) => ({ team_id: String(t.team_id), team_name: String(t.team_name) })))
      } catch {}
    }
    loadTeams()
  }, [])
  return (
    <div className="flex items-center gap-3">
      {user ? (
        <div className="hidden md:flex items-center gap-3 text-sm">
          {teamMembership?.team_name && (
            <span className="text-orange-400">{teamMembership.team_name}</span>
          )}
          <span className="text-gray-300">{user?.email}</span>
          {/* Admin-only Reveal button */}
          {teamMembership?.is_admin && (
            <Button
              size="sm"
              variant="outline"
              className="mx-4 border-amber-400 text-amber-300 hover:bg-amber-900"
              onClick={() => {
                try {
                  const evt = new CustomEvent('uhhp:reveal', {})
                  window.dispatchEvent(evt)
                } catch {}
              }}
            >
              Reveal
            </Button>
          )}
          {teamMembership?.is_admin && (
            <Button
              size="sm"
              variant="outline"
              className="border-emerald-400 text-emerald-300 hover:bg-emerald-900"
              onClick={() => {
                try { window.dispatchEvent(new CustomEvent('uhhp:finalize', {})) } catch {}
              }}
            >
              Finalize
            </Button>
          )}
          <Button onClick={() => logout()} variant="outline" size="sm" className="border-gray-600 text-gray-300 hover:bg-gray-800">
            Logout
          </Button>
        </div>
      ) : (
        <>
          <Button onClick={() => setOpen(true)} size="sm" className="bg-orange-500 hover:bg-orange-600">Login</Button>
          <LoginModal isOpen={open} onClose={() => setOpen(false)} />
        </>
      )}
    </div>
  )
}
