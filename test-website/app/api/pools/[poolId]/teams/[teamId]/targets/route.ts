import { NextRequest, NextResponse } from "next/server"
import { Pool } from "pg"

const fantasyPool = new Pool({ connectionString: process.env.FANTASY_DATABASE_URL })

export async function GET(req: NextRequest, { params }: { params: { poolId: string, teamId: string } }) {
  const { poolId, teamId } = params
  const season = Number(req.nextUrl.searchParams.get("season")) || new Date().getFullYear()
  try {
    const client = await fantasyPool.connect()
    try {
      const res = await client.query(
        `SELECT slot_id, pos, budget, suggested_nhl_player_id
         FROM pool_slot_targets WHERE pool_id=$1 AND season=$2 AND team_id=$3
         ORDER BY slot_id`,
        [poolId, season, teamId]
      )
      return NextResponse.json({ slotTargets: res.rows })
    } finally { client.release() }
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || "internal" }, { status: 500 })
  }
}


