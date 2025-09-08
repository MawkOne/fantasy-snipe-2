import { NextRequest, NextResponse } from "next/server"
import { Pool } from "pg"

const fantasyPool = new Pool({ connectionString: process.env.FANTASY_DATABASE_URL })

export async function POST(req: NextRequest, { params }: { params: { poolId: string } }) {
  const poolId = params.poolId
  const body = await req.json()
  const { pick_id, team_id, amount } = body || {}
  if (!pick_id || !team_id || typeof amount !== "number") {
    return NextResponse.json({ error: "pick_id, team_id, amount required" }, { status: 400 })
  }
  try {
    const client = await fantasyPool.connect()
    try {
      await client.query(
        `INSERT INTO bids(pool_id, pick_id, team_id, amount) VALUES($1,$2,$3,$4)`,
        [poolId, pick_id, team_id, amount],
      )
      return NextResponse.json({ ok: true })
    } finally {
      client.release()
    }
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || "internal" }, { status: 500 })
  }
}


