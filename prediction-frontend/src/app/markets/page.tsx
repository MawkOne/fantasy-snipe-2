// /Users/markhenderson/Cursor Projects/NHL-API/prediction-frontend/src/app/markets/page.tsx
import Link from "next/link";

async function fetchMarkets() {
  const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8100";
  const res = await fetch(`${base}/api/amm/markets`, { next: { revalidate: 0 } });
  if (!res.ok) return [] as any[];
  return res.json();
}

export default async function MarketsPage() {
  const markets = await fetchMarkets();
  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-6 max-w-3xl">
        <h1 className="text-xl font-semibold mb-4">Markets</h1>
        <div className="space-y-3">
          {markets.map((m: any) => (
            <Link key={m.id} href={`/market/${encodeURIComponent(m.slug || m.id)}`} className="block p-4 rounded border border-border/50 hover:bg-accent/30">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">{m.title}</div>
                  <div className="text-xs text-muted-foreground">{m.slug}</div>
                </div>
                <div className="text-sm text-muted-foreground">Yes {(m.prices?.yes*100).toFixed(1)}% · No {(m.prices?.no*100).toFixed(1)}%</div>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
