import { Card } from "@/components/ui/card"

const draftMarkets = [
  {
    title: "James Hagens Destination",
    teams: [
      { name: "San Jose Sharks", abbr: "SJS", probability: 35 },
      { name: "Chicago Blackhawks", abbr: "CHI", probability: 25 },
      { name: "Anaheim Ducks", abbr: "ANA", probability: 18 },
      { name: "Columbus Blue Jackets", abbr: "CBJ", probability: 12 },
      { name: "Montreal Canadiens", abbr: "MTL", probability: 10 },
    ],
  },
  {
    title: "Porter Martone Destination",
    teams: [
      { name: "Chicago Blackhawks", abbr: "CHI", probability: 30 },
      { name: "San Jose Sharks", abbr: "SJS", probability: 28 },
      { name: "Anaheim Ducks", abbr: "ANA", probability: 20 },
      { name: "Columbus Blue Jackets", abbr: "CBJ", probability: 12 },
      { name: "Utah Hockey Club", abbr: "UTA", probability: 10 },
    ],
  },
  {
    title: "Top 5 Pick Markets",
    teams: [
      { name: "San Jose Sharks", abbr: "SJS", probability: 45 },
      { name: "Chicago Blackhawks", abbr: "CHI", probability: 38 },
      { name: "Anaheim Ducks", abbr: "ANA", probability: 32 },
      { name: "Columbus Blue Jackets", abbr: "CBJ", probability: 28 },
      { name: "Montreal Canadiens", abbr: "MTL", probability: 22 },
    ],
  },
]

export function DraftMarketsGrid() {
  return (
    <section>
      <h2 className="text-2xl font-bold mb-4 text-balance">Draft Prospect Markets</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {draftMarkets.map((market) => (
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
