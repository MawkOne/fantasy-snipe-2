import { Card } from "@/components/ui/card"
import Link from "next/link"

const playerMarkets = [
  {
    title: "Goals Leader",
    players: [
      { name: "Auston Matthews", team: "TOR", probability: 22 },
      { name: "Connor McDavid", team: "EDM", probability: 18 },
      { name: "David Pastrnak", team: "BOS", probability: 15 },
      { name: "Leon Draisaitl", team: "EDM", probability: 12 },
      { name: "Nathan MacKinnon", team: "COL", probability: 10 },
    ],
  },
  {
    title: "Points Leader",
    players: [
      { name: "Connor McDavid", team: "EDM", probability: 35 },
      { name: "Nathan MacKinnon", team: "COL", probability: 20 },
      { name: "Nikita Kucherov", team: "TBL", probability: 15 },
      { name: "Leon Draisaitl", team: "EDM", probability: 12 },
      { name: "Auston Matthews", team: "TOR", probability: 8 },
    ],
  },
  {
    title: "Assists Leader",
    players: [
      { name: "Connor McDavid", team: "EDM", probability: 40 },
      { name: "Nikita Kucherov", team: "TBL", probability: 18 },
      { name: "Cale Makar", team: "COL", probability: 12 },
      { name: "Nathan MacKinnon", team: "COL", probability: 10 },
      { name: "Quinn Hughes", team: "VAN", probability: 8 },
    ],
  },
]

export function PlayerMarketsGrid() {
  return (
    <section>
      <h2 className="text-2xl font-bold mb-4 text-balance">Player Performance Forecasts</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {playerMarkets.map((market) => {
          const marketId = market.title.toLowerCase().replace(/\s+/g, "-")

          return (
            <Link key={market.title} href={`/market/multi/${marketId}`}>
              <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
                <h3 className="font-bold text-lg mb-4">{market.title}</h3>
                <div className="space-y-3">
                  {market.players.map((player, index) => (
                    <div key={player.name} className="group cursor-pointer">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm group-hover:text-primary transition-colors truncate">
                            {player.name}
                          </div>
                          <div className="text-xs text-muted-foreground">{player.team}</div>
                        </div>
                        <div className="font-bold ml-2">{player.probability}%</div>
                      </div>
                      {index < market.players.length - 1 && <div className="h-px bg-border mt-3" />}
                    </div>
                  ))}
                </div>
              </Card>
            </Link>
          )
        })}
      </div>
    </section>
  )
}
