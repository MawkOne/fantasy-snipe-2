import { Card } from "@/components/ui/card"

export default async function TeamsPage() {
  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Team Markets</h1>
          <p className="text-muted-foreground">Trade on NHL team performance and outcomes</p>
        </div>

        <Card className="p-8 text-center">
          <div className="max-w-md mx-auto space-y-4">
            <div className="text-6xl">🏒</div>
            <h2 className="text-2xl font-bold">Coming Soon</h2>
            <p className="text-muted-foreground">
              Team prediction markets are currently under development. Soon you'll be able to trade on team performance,
              playoff outcomes, and more.
            </p>
          </div>
        </Card>
      </main>
    </div>
  )
}

