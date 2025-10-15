import { Card } from "@/components/ui/card"

const awardMarkets = [
  {
    title: "Hart Trophy (MVP)",
    subtitle: "Most Valuable Player",
    players: [
      { name: "Connor McDavid", team: "EDM", probability: 45 },
      { name: "Nathan MacKinnon", team: "COL", probability: 25 },
      { name: "Auston Matthews", team: "TOR", probability: 15 },
      { name: "Nikita Kucherov", team: "TBL", probability: 8 },
      { name: "Leon Draisaitl", team: "EDM", probability: 5 },
    ],
  },
  {
    title: "Norris Trophy",
    subtitle: "Best Defenseman",
    players: [
      { name: "Cale Makar", team: "COL", probability: 50 },
      { name: "Quinn Hughes", team: "VAN", probability: 20 },
      { name: "Adam Fox", team: "NYR", probability: 12 },
      { name: "Erik Karlsson", team: "PIT", probability: 8 },
      { name: "Roman Josi", team: "NSH", probability: 6 },
    ],
  },
  {
    title: "Vezina Trophy",
    subtitle: "Best Goaltender",
    players: [
      { name: "Connor Hellebuyck", team: "WPG", probability: 30 },
      { name: "Igor Shesterkin", team: "NYR", probability: 25 },
      { name: "Ilya Sorokin", team: "NYI", probability: 18 },
      { name: "Andrei Vasilevskiy", team: "TBL", probability: 12 },
      { name: "Juuse Saros", team: "NSH", probability: 10 },
    ],
  },
  {
    title: "Calder Trophy",
    subtitle: "Rookie of the Year",
    players: [
      { name: "Connor Bedard", team: "CHI", probability: 55 },
      { name: "Adam Fantilli", team: "CBJ", probability: 20 },
      { name: "Leo Carlsson", team: "ANA", probability: 12 },
      { name: "Matvei Michkov", team: "PHI", probability: 8 },
      { name: "Logan Cooley", team: "ARI", probability: 5 },
    ],
  },
  {
    title: "Selke Trophy",
    subtitle: "Best Defensive Forward",
    players: [
      { name: "Aleksander Barkov", team: "FLA", probability: 35 },
      { name: "Patrice Bergeron", team: "BOS", probability: 25 },
      { name: "Nico Hischier", team: "NJD", probability: 15 },
      { name: "Mark Stone", team: "VGK", probability: 12 },
      { name: "Sebastian Aho", team: "CAR", probability: 10 },
    ],
  },
  {
    title: "Jack Adams Award",
    subtitle: "Coach of the Year",
    players: [
      { name: "Paul Maurice", team: "FLA", probability: 28 },
      { name: "Rod Brind'Amour", team: "CAR", probability: 22 },
      { name: "Jared Bednar", team: "COL", probability: 18 },
      { name: "Peter Laviolette", team: "NYR", probability: 15 },
      { name: "Rick Tocchet", team: "VAN", probability: 12 },
    ],
  },
]

export function AwardMarketsGrid() {
  return (
    <section>
      <h2 className="text-2xl font-bold mb-4 text-balance">NHL Awards Forecasts</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {awardMarkets.map((market) => (
          <Card key={market.title} className="p-6 hover:shadow-lg transition-shadow">
            <div className="mb-4">
              <h3 className="font-bold text-lg">{market.title}</h3>
              <p className="text-sm text-muted-foreground">{market.subtitle}</p>
            </div>
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
        ))}
      </div>
    </section>
  )
}
