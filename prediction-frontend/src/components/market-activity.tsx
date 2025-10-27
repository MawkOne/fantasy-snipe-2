"use client"

interface Trade {
  id: string
  side: string
  outcome: string
  shares: number
  price: number
  cost: number
  created_at: string
  user_id: string
}

interface MarketActivityProps {
  trades: Trade[]
}

export function MarketActivity({ trades = [] }: MarketActivityProps) {
  if (!trades || trades.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">No trades yet</div>
    )
  }

  const formatTimeAgo = (date: string) => {
    const seconds = Math.floor((new Date().getTime() - new Date(date).getTime()) / 1000)
    if (seconds < 60) return `${seconds}s ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
  }

  const formatUserId = (userId: string) => {
    return userId.slice(0, 6)
  }

  return (
    <div className="space-y-3">
      {trades.map((trade) => (
        <div key={trade.id} className="flex items-center justify-between py-2 border-b border-border/50 last:border-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border border-border/50">
              <span className="text-xs font-bold text-primary">{formatUserId(trade.user_id)}</span>
            </div>
            <div className="text-sm">
              <span className="text-foreground">
                {trade.side === "buy" ? "Bought" : "Sold"}{" "}
                <span className="font-semibold">
                  {trade.shares.toFixed(2)} {trade.outcome === "yes" ? "MORE" : "LESS"}
                </span>
              </span>
              <span className="text-muted-foreground"> @ {(trade.price * 100).toFixed(0)}%</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium text-foreground">${trade.cost.toFixed(2)}</div>
            <div className="text-xs text-muted-foreground">{formatTimeAgo(trade.created_at)}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

