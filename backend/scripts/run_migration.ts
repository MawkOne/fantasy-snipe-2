import fs from "fs"
import path from "path"
import { Pool } from "pg"
import "dotenv/config"

async function main() {
  const conn = process.env.FANTASY_DATABASE_URL
  if (!conn) {
    console.error("FANTASY_DATABASE_URL not set")
    process.exit(1)
  }
  const pool = new Pool({ connectionString: conn })
  const sqlPath = path.resolve(__dirname, "../sql/001_init_fantasy.sql")
  const sql = fs.readFileSync(sqlPath, "utf8")
  const client = await pool.connect()
  try {
    await client.query(sql)
    console.log("Migration applied successfully")
  } finally {
    client.release()
    await pool.end()
  }
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})


