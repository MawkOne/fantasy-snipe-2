import { NextResponse } from "next/server"
import fs from "fs/promises"
import path from "path"

type SourceRank = {
  source: string
  rank: number
}

type PlayerEntry = {
  name: string
  ranks: SourceRank[]
  blended: number
}

function normalizeName(name: string): string {
  return name
    .trim()
    .replace(/\s+/g, " ")
    .replace(/\./g, "")
    .toLowerCase()
}

function simpleCsvParse(csv: string): { headers: string[]; rows: string[][] } {
  const lines = csv.split(/\r?\n/).filter((l) => l.trim() !== "")
  if (lines.length === 0) return { headers: [], rows: [] }
  const headers = lines[0].split(",").map((h) => h.trim())
  const rows = lines.slice(1).map((line) => line.split(",").map((c) => c.trim()))
  return { headers, rows }
}

// Heuristic: choose a numeric column likely representing projected or fantasy points
function choosePointsColumn(headers: string[]): number {
  const preferred = [
    /^(proj\s*)?points?$/i,
    /^pts$/i,
    /fantasy\s*points/i,
    /^fp$/i,
    /total\s*points/i,
    /proj/i,
  ]
  for (const re of preferred) {
    const idx = headers.findIndex((h) => re.test(h))
    if (idx !== -1) return idx
  }
  // Fallback: first numeric-looking column after name
  for (let i = 0; i < headers.length; i++) {
    if (/name|player/i.test(headers[i])) continue
    return i
  }
  return -1
}

async function parseAnyTabular(filePath: string): Promise<Array<{ name: string; value: number }>> {
  const content = await fs.readFile(filePath, "utf8")
  // Prefer CSV
  let { headers, rows } = simpleCsvParse(content)
  if (headers.length < 2 || rows.length === 0) {
    // Try TSV
    const lines = content.split(/\r?\n/).filter(Boolean)
    if (lines.length > 1 && lines[0].includes("\t")) {
      headers = lines[0].split("\t").map((h) => h.trim())
      rows = lines.slice(1).map((l) => l.split("\t").map((c) => c.trim()))
    }
  }
  if (headers.length < 2 || rows.length === 0) return []
  const nameIdx = headers.findIndex((h) => /player|name/i.test(h))
  const ptsIdx = choosePointsColumn(headers)
  if (nameIdx === -1 || ptsIdx === -1) return []
  const entries: Array<{ name: string; value: number }> = []
  for (const r of rows) {
    const n = (r[nameIdx] || "").trim()
    const v = parseFloat(r[ptsIdx] || "")
    if (n && Number.isFinite(v)) entries.push({ name: n, value: v })
  }
  return entries
}

async function loadDirectoryAsRanking(dirPath: string): Promise<Map<string, number>> {
  let dirEntries: string[] = []
  try {
    const items = await fs.readdir(dirPath, { withFileTypes: true })
    dirEntries = items.filter((i) => i.isFile()).map((i) => path.join(dirPath, i.name))
  } catch {
    return new Map()
  }
  const scores = new Map<string, number>()
  for (const file of dirEntries) {
    try {
      const entries = await parseAnyTabular(file)
      for (const e of entries) {
        const key = normalizeName(e.name)
        const prev = scores.get(key)
        // Use max score across files within the same directory
        if (prev === undefined || e.value > prev) scores.set(key, e.value)
      }
    } catch {
      // skip unreadable file
    }
  }
  // Turn scores into ranks (higher value => better rank 1)
  const sorted = [...scores.entries()].sort((a, b) => b[1] - a[1])
  const ranks = new Map<string, number>()
  sorted.forEach(([key], idx) => ranks.set(key, idx + 1))
  return ranks
}

export async function GET() {
  try {
    const root = "/Users/markhenderson/Cursor Projects/NHL-API/Projections/2025"
    const sourceDirs = [
      path.join(root, "AG_skaters"),
      path.join(root, "Cullen_goalies"),
      path.join(root, "Cullen_skaters"),
      path.join(root, "DFO_goalies"),
      path.join(root, "DFO_skaters"),
      path.join(root, "DtZ"),
      path.join(root, "DTZ_goalies"),
      path.join(root, "FHFH_skaters"),
      path.join(root, "kubuto"),
      path.join(root, "Laidlaw"),
    ]

    const rankingsPerDir = await Promise.all(sourceDirs.map((d) => loadDirectoryAsRanking(d)))

    // Collect all player keys
    const keys = new Set<string>()
    for (const r of rankingsPerDir) for (const k of r.keys()) keys.add(k)
    const defaultRank = 999
    const players: PlayerEntry[] = []

    for (const key of keys) {
      const ranks: SourceRank[] = []
      rankingsPerDir.forEach((r, idx) => {
        const val = r.get(key)
        if (val !== undefined) ranks.push({ source: path.basename(sourceDirs[idx]), rank: val })
      })
      if (ranks.length === 0) continue
      const present = ranks.length
      const missing = sourceDirs.length - present
      const sum = ranks.reduce((acc, r) => acc + r.rank, 0) + missing * defaultRank
      const blended = sum / sourceDirs.length
      const displayName = key
        .split(" ")
        .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
        .join(" ")
      players.push({ name: displayName, ranks, blended })
    }

    players.sort((a, b) => a.blended - b.blended)
    const top50 = players.slice(0, 50)

    return NextResponse.json({ count: top50.length, players: top50 })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}


