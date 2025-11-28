import { NextRequest, NextResponse } from "next/server"
import { Pool } from "pg"

const fantasyPool = new Pool({ connectionString: process.env.FANTASY_DATABASE_URL })
const nhlPool = new Pool({ connectionString: process.env.NHL_DATABASE_URL, max: 5 })

export async function GET(req: NextRequest, { params }: { params: { poolId: string } }) {
  const poolId = params.poolId
  const season = Number(req.nextUrl.searchParams.get("season")) || new Date().getFullYear()
  try {
    const client = await fantasyPool.connect()
    try {
      const [orderRes, picksRes, teamsRes, targetsRes] = await Promise.all([
        client.query("SELECT order_list as order FROM auction_orders WHERE pool_id=$1 AND season=$2 ORDER BY updated_at DESC LIMIT 1", [poolId, season]),
        client.query("SELECT pick_no, nhl_player_id, team_id, pos, price FROM auction_picks WHERE pool_id=$1 AND season=$2 ORDER BY pick_no ASC", [poolId, season]),
        client.query("SELECT id, name, abbrev FROM pool_teams WHERE pool_id=$1 ORDER BY name", [poolId]),
        client.query("SELECT team_id, slot_id, pos, budget, suggested_nhl_player_id FROM pool_slot_targets WHERE pool_id=$1 AND season=$2", [poolId, season]),
      ])
      const order = orderRes.rows?.[0]?.order || []
      const picks = picksRes.rows || []
      const teams = teamsRes.rows || []
      const slotTargets = targetsRes.rows || []
      return NextResponse.json({ order, picks, teams, slotTargets, season })
    } finally {
      client.release()
    }
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || "internal" }, { status: 500 })
  }
}


