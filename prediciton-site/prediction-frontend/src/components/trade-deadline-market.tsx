import { Card } from "@/components/ui/card"
import { TrendingUp } from "lucide-react"

const players = [
  { name: "Elias Pettersson", team: "VAN", abbr: "EP", probability: 45, color: "bg-blue-600" },
  { name: "Mitch Marner", team: "TOR", abbr: "MM", probability: 38, color: "bg-blue-500" },
  { name: "Mikko Rantanen", team: "COL", abbr: "MR", probability: 32, color: "bg-blue-600" },
  { name: "Brady Tkachuk", team: "OTT", abbr: "BT", probability: 28, color: "bg-red-600" },
  { name: "J.T. Miller", team: "VAN", abbr: "JM", probability: 25, color: "bg-blue-600" },
  { name: "Chris Kreider", team: "NYR", abbr: "CK", probability: 22, color: "bg-blue-600" },
  { name: "Brock Boeser", team: "VAN", abbr: "BB", probability: 18, color: "bg-blue-600" },
  { name: "Jakob Chychrun", team: "OTT", abbr: "JC", probability: 15, color: "bg-red-600" },
]

export function TradeDeadlineMarket() {
  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-balance">Most Likely to be Traded</h2>
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
                    style={{ width: `${player.probability * 2}%` }}
                  />
                </div>
              </div>
              {index < 3 && <TrendingUp className="w-4 h-4 text-secondary flex-shrink-0" />}
            </div>
          ))}
        </div>
      </Card>
    </section>
  )
}
