import { NextRequest, NextResponse } from "next/server"
import { Pool } from "pg"

const fantasyPool = new Pool({ connectionString: process.env.FANTASY_DATABASE_URL })

export async function GET(req: NextRequest, { params }: { params: { poolId: string } }) {
  const poolId = params.poolId
  const season = Number(req.nextUrl.searchParams.get("season")) || new Date().getFullYear()
  try {
    const client = await fantasyPool.connect()
    try {
      const res = await client.query(
        "SELECT order_list as order FROM auction_orders WHERE pool_id=$1 AND season=$2 ORDER BY updated_at DESC LIMIT 1",
        [poolId, season],
      )
      return NextResponse.json({ order: res.rows?.[0]?.order || [] })
    } finally {
      client.release()
    }
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || "internal" }, { status: 500 })
  }
}

export async function PUT(req: NextRequest, { params }: { params: { poolId: string } }) {
  const poolId = params.poolId
  const season = Number(req.nextUrl.searchParams.get("season")) || new Date().getFullYear()
  const body = await req.json()
  const order = Array.isArray(body?.order) ? body.order : []
  if (!order.length) return NextResponse.json({ error: "order required" }, { status: 400 })
  try {
    const client = await fantasyPool.connect()
    try {
      await client.query(
        `INSERT INTO auction_orders(id, pool_id, season, order_list, updated_at)
         VALUES(gen_random_uuid()::text, $1, $2, $3::jsonb, now())
         ON CONFLICT (id) DO NOTHING`,
        [poolId, season, JSON.stringify(order)],
      )
      // Keep only latest by inserting new version; consumers always read last updated
      return NextResponse.json({ ok: true })
    } finally {
      client.release()
    }
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || "internal" }, { status: 500 })
  }
}


