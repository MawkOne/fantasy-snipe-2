import { Card } from "@/components/ui/card"

const tradeMarkets = [
  {
    title: "Elias Pettersson Destination",
    teams: [
      { name: "Carolina Hurricanes", abbr: "CAR", probability: 28 },
      { name: "New York Rangers", abbr: "NYR", probability: 22 },
      { name: "Vegas Golden Knights", abbr: "VGK", probability: 18 },
      { name: "Dallas Stars", abbr: "DAL", probability: 15 },
      { name: "Boston Bruins", abbr: "BOS", probability: 12 },
    ],
  },
  {
    title: "Mitch Marner Destination",
    teams: [
      { name: "Vegas Golden Knights", abbr: "VGK", probability: 25 },
      { name: "Dallas Stars", abbr: "DAL", probability: 20 },
      { name: "Carolina Hurricanes", abbr: "CAR", probability: 18 },
      { name: "Nashville Predators", abbr: "NSH", probability: 15 },
      { name: "Utah Hockey Club", abbr: "UTA", probability: 12 },
    ],
  },
  {
    title: "Mikko Rantanen Destination",
    teams: [
      { name: "New York Rangers", abbr: "NYR", probability: 30 },
      { name: "Carolina Hurricanes", abbr: "CAR", probability: 22 },
      { name: "Boston Bruins", abbr: "BOS", probability: 18 },
      { name: "Tampa Bay Lightning", abbr: "TBL", probability: 15 },
      { name: "Florida Panthers", abbr: "FLA", probability: 10 },
    ],
  },
]

export function TradeMarketsGrid() {
  return (
    <section>
      <h2 className="text-2xl font-bold mb-4 text-balance">Trade Destination Markets</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tradeMarkets.map((market) => (
          <Card key={market.title} className="p-6">
            <h3 className="font-bold text-lg mb-4">{market.title}</h3>
            <div className="space-y-3">
              {market.teams.map((team, index) => (
                <div key={team.abbr} className="group cursor-pointer">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm group-hover:text-primary transition-colors truncate">
                        {team.name}
                      </div>
                      <div className="text-xs text-muted-foreground">{team.abbr}</div>
                    </div>
                    <div className="font-bold ml-2">{team.probability}%</div>
                  </div>
                  {index < market.teams.length - 1 && <div className="h-px bg-border mt-3" />}
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </section>
  )
}
