import { Pool } from "pg"

let pool: Pool | null = null

export function getDb() {
  if (!pool) {
    const connectionString = process.env.MARKET_DATABASE_URL || process.env.DATABASE_URL
    if (!connectionString) throw new Error("DATABASE_URL not set")
    pool = new Pool({ connectionString, max: 5 })
  }
  return pool
}


