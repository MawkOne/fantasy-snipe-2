import { NextResponse } from "next/server"
import { getDb } from "@/lib/db"

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { slug, title, description, b } = body || {}
    if (!slug || !title || !b || Number(b) <= 0) {
      return NextResponse.json({ error: "slug, title, b required" }, { status: 400 })
    }
    const pool = getDb()
    const client = await pool.connect()
    try {
      await client.query("BEGIN")
      const ins = await client.query(
        `INSERT INTO markets (slug, title, description, outcome_type, status, b)
         VALUES ($1,$2,$3,'binary','draft',$4) RETURNING id`,
        [slug, title, description || null, b]
      )
      const marketId = ins.rows[0].id as string
      await client.query(
        `INSERT INTO market_outcomes (market_id, outcome) VALUES ($1,'yes'),($1,'no')`,
        [marketId]
      )
      await client.query(
        `INSERT INTO amm_inventory (market_id, outcome, shares) VALUES ($1,'yes',0),($1,'no',0)`,
        [marketId]
      )
      await client.query("COMMIT")
      return NextResponse.json({ id: marketId })
    } catch (e: any) {
      await client.query("ROLLBACK")
      throw e
    } finally {
      client.release()
    }
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}


