import { NextResponse } from "next/server"
import { computeBlendedTop50 } from "@/lib/blended"

export async function GET() {
  try {
    const top50 = await computeBlendedTop50()
    return NextResponse.json({ count: top50.length, players: top50 })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}


