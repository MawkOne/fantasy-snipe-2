import { NextResponse } from "next/server"
import { GET as blendedGET } from "@/app/api/blended-top50/route"
import { getPlayerHeadshotUrlByName } from "@/lib/nhl"

export async function GET() {
  // Reuse the blended computation by fetching from the internal handler
  // We import and call it indirectly by emulating its logic via a fetch to the internal endpoint is not available here,
  // so we call it by reusing the module's export through a dummy request is not ideal.
  // Instead, we re-invoke the blended endpoint and augment results.
  const resp = await blendedGET()
  const json = await resp.json()
  if (json?.players && Array.isArray(json.players)) {
    const players = await Promise.all(
      json.players.map(async (p: any) => ({
        ...p,
        headshot: await getPlayerHeadshotUrlByName(p.name),
      }))
    )
    return NextResponse.json({ count: players.length, players })
  }
  return resp
}


