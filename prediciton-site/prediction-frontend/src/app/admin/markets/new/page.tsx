"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function NewMarketPage() {
  const [slug, setSlug] = useState("")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [b, setB] = useState("50")
  const [status, setStatus] = useState<"idle"|"saving"|"done"|"error">("idle")
  const [error, setError] = useState<string|undefined>()

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setStatus("saving")
    setError(undefined)
    try {
      const resp = await fetch("/api/admin/markets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slug, title, description, b: Number(b) })
      })
      if (!resp.ok) {
        const j = await resp.json().catch(() => ({}))
        throw new Error(j?.error || `HTTP ${resp.status}`)
      }
      setStatus("done")
    } catch (e: any) {
      setError(e.message)
      setStatus("error")
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 max-w-2xl">
        <Card className="p-6">
          <h1 className="text-xl font-semibold mb-4">Create Binary Market</h1>
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Slug</label>
              <input className="w-full p-2 rounded border border-border bg-background" value={slug} onChange={(e) => setSlug(e.target.value)} required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Title</label>
              <input className="w-full p-2 rounded border border-border bg-background" value={title} onChange={(e) => setTitle(e.target.value)} required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea className="w-full p-2 rounded border border-border bg-background" value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Liquidity (b)</label>
              <input type="number" step="0.01" className="w-full p-2 rounded border border-border bg-background" value={b} onChange={(e) => setB(e.target.value)} required />
            </div>
            <div className="flex items-center gap-3">
              <Button type="submit" disabled={status==="saving"}>{status==="saving"?"Saving...":"Create Market"}</Button>
              {status==="done" && <span className="text-sm text-green-600">Created.</span>}
              {status==="error" && <span className="text-sm text-red-600">{error}</span>}
            </div>
          </form>
        </Card>
      </main>
    </div>
  )
}


