import { Card } from "@/components/ui/card"

export default async function TradesPage() {
  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Trade Activity</h1>
          <p className="text-muted-foreground">View recent trades and market activity</p>
        </div>

        <Card className="p-8 text-center">
          <div className="max-w-md mx-auto space-y-4">
            <div className="text-6xl">📊</div>
            <h2 className="text-2xl font-bold">Coming Soon</h2>
            <p className="text-muted-foreground">
              Trade history and activity feeds are currently under development. Soon you'll be able to see all market
              activity, track your trades, and analyze market movements.
            </p>
          </div>
        </Card>
      </main>
    </div>
  )
}
