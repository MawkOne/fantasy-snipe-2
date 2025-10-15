const nameToId: Record<string, string> = {
  "Connor McDavid": "8478402",
  "Auston Matthews": "8479318",
  "Nathan MacKinnon": "8477492",
  "David Pastrnak": "8477956",
  "Cale Makar": "8480069",
  "Igor Shesterkin": "8480045",
  "Leon Draisaitl": "8477934",
  "Nikita Kucherov": "8476453",
  "Connor Hellebuyck": "8476945",
  "Artemi Panarin": "8478550",
  "Matthew Tkachuk": "8479314",
  "Quinn Hughes": "8480800",
}

export async function getPlayerHeadshotUrlById(playerId: string): Promise<string | null> {
  try {
    const res = await fetch(`https://api-web.nhle.com/v1/player/${playerId}/landing`, {
      // Cache for 1 day
      next: { revalidate: 86400 },
    })
    if (!res.ok) return null
    const data = await res.json()
    return typeof data?.headshot === "string" ? data.headshot : null
  } catch {
    return null
  }
}

export async function getPlayerHeadshotUrlByName(name: string): Promise<string | null> {
  const id = nameToId[name]
  if (!id) return null
  return await getPlayerHeadshotUrlById(id)
}


