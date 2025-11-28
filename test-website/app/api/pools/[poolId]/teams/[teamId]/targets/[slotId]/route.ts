import { NextRequest, NextResponse } from "next/server"
import { Pool } from "pg"

const fantasyPool = new Pool({ connectionString: process.env.FANTASY_DATABASE_URL })

export async function PUT(req: NextRequest, { params }: { params: { poolId: string, teamId: string, slotId: string } }) {
  const poolId = params.poolId
  const teamId = params.teamId
  const slotId = params.slotId
  const season = Number(req.nextUrl.searchParams.get("season")) || new Date().getFullYear()
  const body = await req.json()
  const budget = body?.budget as number | undefined
  const suggested = body?.suggested_nhl_player_id as number | undefined
  try {
    const client = await fantasyPool.connect()
    try {
      await client.query(
        `INSERT INTO pool_slot_targets(pool_id, season, team_id, slot_id, pos, budget, suggested_nhl_player_id)
         VALUES($1,$2,$3,$4,COALESCE($5,'RES'),$6,$7)
         ON CONFLICT(pool_id, season, team_id, slot_id)
         DO UPDATE SET budget=COALESCE($6, pool_slot_targets.budget), suggested_nhl_player_id=COALESCE($7, pool_slot_targets.suggested_nhl_player_id), updated_at=now()`,
        [poolId, season, teamId, slotId, body?.pos, budget ?? null, suggested ?? null]
      )
      return NextResponse.json({ ok: true })
    } finally { client.release() }
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || "internal" }, { status: 500 })
  }
}


