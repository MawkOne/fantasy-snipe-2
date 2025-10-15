import { NextResponse } from "next/server"
import { computeBlendedTop50 } from "@/lib/blended"
import { getPlayerHeadshotUrlByName } from "@/lib/nhl"

export async function GET() {
  const base = await computeBlendedTop50()
  const players = await Promise.all(
    base.map(async (p) => ({ ...p, headshot: await getPlayerHeadshotUrlByName(p.name) }))
  )
  return NextResponse.json({ count: players.length, players })
}


