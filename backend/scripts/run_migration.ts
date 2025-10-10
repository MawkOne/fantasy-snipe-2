import fs from "fs"
import path from "path"
import { fileURLToPath } from "url"
import { Pool } from "pg"
import "dotenv/config"

async function main() {
  const conn = process.env.FANTASY_DATABASE_URL
  if (!conn) {
    console.error("FANTASY_DATABASE_URL not set")
    process.exit(1)
  }
  const pool = new Pool({ connectionString: conn })
  const __filename = fileURLToPath(import.meta.url)
  const __dirname_local = path.dirname(__filename)
  const sqlDir = path.resolve(__dirname_local, "../sql")
  const files = fs
    .readdirSync(sqlDir)
    .filter((f) => f.toLowerCase().endsWith(".sql"))
    .sort((a, b) => a.localeCompare(b))

  const client = await pool.connect()
  try {
    for (const f of files) {
      const sqlPath = path.join(sqlDir, f)
      const sql = fs.readFileSync(sqlPath, "utf8")
      console.log(`Applying migration: ${f}`)
      await client.query(sql)
    }
    console.log("All migrations applied successfully")
  } finally {
    client.release()
    await pool.end()
  }
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})


