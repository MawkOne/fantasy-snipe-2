export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({} as any))
    const code = String(body?.code || "")
    const redirectUri = String(body?.redirectUri || "")
    const domain = process.env.NEXT_PUBLIC_KINDE_DOMAIN
    const clientId = process.env.NEXT_PUBLIC_KINDE_CLIENT_ID
    const clientSecret = process.env.KINDE_CLIENT_SECRET
    if (!code || !redirectUri) {
      return new Response(JSON.stringify({ error: "missing_code_or_redirect_uri" }), { status: 400 })
    }
    if (!domain || !clientId || !clientSecret) {
      return new Response(JSON.stringify({ error: "server_env_missing" }), { status: 500 })
    }
    const tokenUrl = `https://${domain}/oauth2/token`
    const payload = new URLSearchParams()
    payload.set("grant_type", "authorization_code")
    payload.set("code", code)
    payload.set("redirect_uri", redirectUri)
    payload.set("client_id", clientId)
    payload.set("client_secret", clientSecret)
    const tokenRes = await fetch(tokenUrl, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: payload.toString(),
      cache: "no-store",
    })
    if (!tokenRes.ok) {
      const err = await tokenRes.text().catch(() => "")
      return new Response(JSON.stringify({ error: "token_exchange_failed", detail: err }), { status: 502 })
    }
    const tokens = await tokenRes.json()
    const accessToken = tokens?.access_token as string | undefined
    // Try userinfo endpoint for profile
    let profile: any = null
    if (accessToken) {
      try {
        const uiRes = await fetch(`https://${domain}/oauth2/userinfo`, {
          headers: { Authorization: `Bearer ${accessToken}` },
          cache: "no-store",
        })
        if (uiRes.ok) {
          profile = await uiRes.json()
        }
      } catch {}
    }
    return new Response(JSON.stringify({ tokens, profile }), { status: 200 })
  } catch (e: any) {
    return new Response(JSON.stringify({ error: "server_error", detail: String(e?.message || e) }), { status: 500 })
  }
}


