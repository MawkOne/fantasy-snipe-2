import { NextRequest, NextResponse } from "next/server"
import { Pool } from "pg"

const fantasyPool = new Pool({ connectionString: process.env.FANTASY_DATABASE_URL })

export async function POST(req: NextRequest, { params }: { params: { poolId: string } }) {
  const poolId = params.poolId
  const body = await req.json()
  const season = Number(body?.season || new Date().getFullYear())
  const { pick_no, nhl_player_id, team_id, pos, price } = body || {}
  if (!pick_no || !nhl_player_id || !team_id || !price) {
    return NextResponse.json({ error: "pick_no, nhl_player_id, team_id, price required" }, { status: 400 })
  }
  try {
    const client = await fantasyPool.connect()
    try {
      await client.query("BEGIN")
      await client.query(
        `INSERT INTO auction_picks(pool_id, season, pick_no, nhl_player_id, team_id, pos, price)
         VALUES($1,$2,$3,$4,$5,$6,$7)
         ON CONFLICT(pool_id, season, pick_no) DO UPDATE SET nhl_player_id=EXCLUDED.nhl_player_id, team_id=EXCLUDED.team_id, pos=EXCLUDED.pos, price=EXCLUDED.price`,
        [poolId, season, pick_no, nhl_player_id, team_id, pos || null, price],
      )
      await client.query("COMMIT")
      return NextResponse.json({ ok: true })
    } catch (e) {
      await fantasyPool.query("ROLLBACK")
      throw e
    } finally {
      client.release()
    }
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || "internal" }, { status: 500 })
  }
}


