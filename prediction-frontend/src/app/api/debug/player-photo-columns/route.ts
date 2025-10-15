import { NextResponse } from "next/server"
import { Client } from "pg"

export async function GET() {
  const connStr = process.env.DATABASE_URL || "postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require"
  const client = new Client({ connectionString: connStr })

  try {
    await client.connect()

    const columnsRes = await client.query(
      `select column_name
       from information_schema.columns
       where table_schema='public' and table_name='player_details'
         and (column_name ilike '%url%' or column_name ilike '%image%' or column_name ilike '%photo%')
       order by column_name`
    )

    const columns: string[] = columnsRes.rows.map((r) => r.column_name)

    const samples: Record<string, Array<{ value: string }>> = {}

    for (const col of columns) {
      const sampleRes = await client.query(
        `select ${col} as value from public.player_details where ${col} is not null and ${col} <> '' limit 5`
      )
      samples[col] = sampleRes.rows
    }

    return NextResponse.json({ columns, samples })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  } finally {
    try { await client.end() } catch {}
  }
}
