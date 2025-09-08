import { NextResponse } from "next/server"
import path from "path"
import fs from "fs/promises"

export async function GET(req: Request) {
  try {
    const url = new URL(req.url)
    const useMock = url.searchParams.get("mock") === "1"

    const projectRoot = path.resolve(process.cwd(), "..")
    const auctionPath = useMock
      ? path.resolve(projectRoot, "uhhp_simulations/stage4/stage4_auction_mock.json")
      : path.resolve(projectRoot, "uhhp_simulations/stage4/stage4_auction.json")
    const outlookPrePath = path.resolve(projectRoot, "uhhp_simulations/outputs/stage4_team_outlooks_pre.json")
    const clustersPath = path.resolve(projectRoot, "uhhp_simulations/outputs/fp_clusters_tiers8.json")
    const stage1Path = path.resolve(projectRoot, "uhhp_simulations/outputs/stage1_rollforward.json")
    const stage1AltPath = path.resolve(projectRoot, "uhhp_simulations/stage1/stage1_rollforward.json")
    const projectionsMockPath = path.resolve(projectRoot, "uhhp_simulations/stage4/projections_mock.json")

    let [auctionRaw, outlookRaw, clustersRaw, stage1Raw, projMockRaw] = await Promise.all([
      fs.readFile(auctionPath, "utf-8").catch(() => "{}"),
      fs.readFile(outlookPrePath, "utf-8").catch(() => "{}"),
      fs.readFile(clustersPath, "utf-8").catch(() => "{}"),
      fs.readFile(stage1Path, "utf-8").catch(() => "{}"),
      fs.readFile(projectionsMockPath, "utf-8").catch(() => "{}"),
    ])

    // Fallback to stage1/ directory if outputs file missing
    if (!stage1Raw || stage1Raw.trim() === "{}") {
      try {
        stage1Raw = await fs.readFile(stage1AltPath, "utf-8")
      } catch {}
    }

    const auction = JSON.parse(auctionRaw || "{}")
    const outlook = JSON.parse(outlookRaw || "{}")
    const clusters = JSON.parse(clustersRaw || "{}")
    const stage1 = JSON.parse(stage1Raw || "{}")
    const projectionsMock = JSON.parse(projMockRaw || "{}")

    // Build fp map from clusters assignments or mock projections
    const fpMap: Record<string, number> = {}
    if (useMock && Array.isArray(projectionsMock?.players)) {
      for (const p of projectionsMock.players) {
        const name: string = (p?.player || "").toString().trim().toLowerCase()
        const fpVal = typeof p?.fp === "number" ? p.fp : parseFloat(String(p?.fp || 0))
        if (name) fpMap[name] = fpVal
      }
    } else {
      for (const pos of ["C", "W", "D", "G"]) {
        const info = clusters?.[pos]
        const assigns = info?.assignments || []
        for (const a of assigns) {
          const name: string = (a?.name || "").toString().trim().toLowerCase()
          const fpVal = typeof a?.fp === "number" ? a.fp : parseFloat(String(a?.fp || 0))
          if (name) fpMap[name] = fpVal
        }
      }
    }

    // Build age map from stage1 birthdates
    const ageMap: Record<string, number> = {}
    const cutoff = new Date("2025-07-01")
    function computeAge(dstr?: string): number | null {
      if (!dstr) return null
      const d = new Date(dstr)
      if (isNaN(d.getTime())) return null
      let age = cutoff.getFullYear() - d.getFullYear()
      const m = cutoff.getMonth() - d.getMonth()
      if (m < 0 || (m === 0 && cutoff.getDate() < d.getDate())) age--
      return age
    }
    try {
      const fas = (stage1?.free_agents as any[]) || []
      for (const fa of fas) {
        const nm = (fa?.player || "").toString().trim().toLowerCase()
        const bd = (fa?.birthdate || "") as string
        const age = computeAge(bd)
        if (nm && age !== null) ageMap[nm] = age
      }
      const teams = (stage1?.teams as any[]) || []
      for (const t of teams) {
        const players = (t?.players as any[]) || []
        for (const pl of players) {
          const nm = (pl?.player || pl?.player_full_name || pl?.display_name || "").toString().trim().toLowerCase()
          const bd = (pl?.birthdate || "") as string
          const age = computeAge(bd)
          if (nm && age !== null) ageMap[nm] = age
        }
      }
    } catch {}

    // Build projections array for right panel
    const faTypeMap: Record<string, string> = {}
    try {
      const fas = (stage1?.free_agents as any[]) || []
      for (const fa of fas) {
        const nm = (fa?.player || "").toString().trim().toLowerCase()
        const typ = (fa?.fa_type || "").toString().trim().toUpperCase()
        if (nm) faTypeMap[nm] = typ || "UFA"
      }
    } catch {}

    let projections: any[] = []
    if (useMock && Array.isArray(projectionsMock?.players)) {
      projections = projectionsMock.players
    } else {
      for (const pos of ["C", "W", "D", "G"]) {
        const assigns = clusters?.[pos]?.assignments || []
        for (const a of assigns) {
          const nameRaw = (a?.name || "").toString()
          const name = nameRaw.trim()
          if (!name) continue
          const key = name.toLowerCase()
          const fpVal = typeof a?.fp === "number" ? a.fp : parseFloat(String(a?.fp || 0))
          const type = (faTypeMap[key] || "UFA").toUpperCase()
          projections.push({ player: name, pos, fp: fpVal, type })
        }
      }
    }

    // Build stage1 teams, and attach RFAs to owning team roster
    const stage1TeamsBase: any[] = Array.isArray(stage1?.teams) ? JSON.parse(JSON.stringify(stage1.teams)) : []
    try {
      const fas = (stage1?.free_agents as any[]) || []
      // Map team_name -> team object
      const nameToTeam: Record<string, any> = {}
      for (const t of stage1TeamsBase) {
        const key = (t?.team_name || t?.team || "").toString()
        if (key) nameToTeam[key] = t
        if (!Array.isArray(t.players)) t.players = []
      }
      for (const fa of fas) {
        const typ = (fa?.fa_type || "").toString().toUpperCase()
        if (typ !== "RFA") continue
        const teamName = (fa?.team || "").toString()
        const team = nameToTeam[teamName]
        if (!team) continue
        const players: any[] = team.players || (team.players = [])
        const pname = (fa?.player || fa?.player_full_name || "").toString()
        const exists = players.some((p) => ((p?.player || p?.player_full_name || "").toString() === pname))
        if (exists) continue
        const posRaw = (fa?.pos || "").toString().toUpperCase()
        const pos = posRaw === "LW" || posRaw === "RW" ? "W" : (posRaw || "F")
        const salary = Number(fa?.last_salary || 0)
        players.push({
          player: pname,
          pos,
          salary,
          years: 0,
          future_fa: "RFA",
          player_id: fa?.player_id,
          player_full_name: fa?.player_full_name || pname,
        })
      }
    } catch {}
    const stage1Teams = stage1TeamsBase
    return NextResponse.json({ auction, outlook, fpMap, ageMap, projections, stage1Teams, mock: useMock })
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
