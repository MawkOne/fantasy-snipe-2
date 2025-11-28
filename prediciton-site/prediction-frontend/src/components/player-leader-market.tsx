import { Card } from "@/components/ui/card"

const players = [
  { name: "Connor McDavid", team: "EDM", abbr: "CM", probability: 35, color: "bg-orange-600" },
  { name: "Nathan MacKinnon", team: "COL", abbr: "NM", probability: 20, color: "bg-blue-600" },
  { name: "Auston Matthews", team: "TOR", abbr: "AM", probability: 15, color: "bg-blue-500" },
  { name: "Nikita Kucherov", team: "TBL", abbr: "NK", probability: 12, color: "bg-blue-700" },
  { name: "Leon Draisaitl", team: "EDM", abbr: "LD", probability: 8, color: "bg-orange-600" },
  { name: "David Pastrnak", team: "BOS", abbr: "DP", probability: 5, color: "bg-yellow-600" },
  { name: "Cale Makar", team: "COL", abbr: "CM", probability: 3, color: "bg-blue-600" },
  { name: "Artemi Panarin", team: "NYR", abbr: "AP", probability: 2, color: "bg-blue-600" },
]

export function PlayerLeaderMarket() {
  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-balance">Points Leader</h2>
        <button className="text-sm text-primary font-medium hover:underline">Show More</button>
      </div>
      <Card className="p-6">
        <div className="space-y-3">
          {players.map((player, index) => (
            <div key={player.name} className="flex items-center gap-4 group cursor-pointer">
              <div
                className={`w-10 h-10 rounded-lg ${player.color} flex items-center justify-center text-white font-bold text-xs flex-shrink-0`}
              >
                {player.abbr}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <div>
                    <span className="font-medium group-hover:text-primary transition-colors">{player.name}</span>
                    <span className="text-sm text-muted-foreground ml-2">{player.team}</span>
                  </div>
                  <span className="font-bold text-lg">{player.probability}%</span>
                </div>
                <div className="h-2 bg-accent rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all group-hover:bg-primary/80"
                    style={{ width: `${player.probability * 2.5}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </section>
  )
}
