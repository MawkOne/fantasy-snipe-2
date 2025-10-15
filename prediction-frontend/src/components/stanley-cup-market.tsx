import { Card } from "@/components/ui/card"

const teams = [
  { name: "Avalanche", abbr: "COL", probability: 18, color: "bg-[#6F263D]" },
  { name: "Panthers", abbr: "FLA", probability: 15, color: "bg-[#C8102E]" },
  { name: "Hurricanes", abbr: "CAR", probability: 12, color: "bg-[#CC0000]" },
  { name: "Oilers", abbr: "EDM", probability: 11, color: "bg-[#FF4C00]" },
  { name: "Rangers", abbr: "NYR", probability: 10, color: "bg-[#0038A8]" },
  { name: "Maple Leafs", abbr: "TOR", probability: 8, color: "bg-[#00205B]" },
  { name: "Bruins", abbr: "BOS", probability: 7, color: "bg-[#FFB81C]" },
  { name: "Stars", abbr: "DAL", probability: 6, color: "bg-[#006847]" },
  { name: "Golden Knights", abbr: "VGK", probability: 5, color: "bg-[#B4975A]" },
  { name: "Devils", abbr: "NJD", probability: 4, color: "bg-[#CE1126]" },
]

export function StanleyCupMarket() {
  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-balance">Stanley Cup Champion Forecast</h2>
        <button className="text-sm text-primary font-medium hover:underline">Show More</button>
      </div>
      <Card className="p-6">
        <div className="space-y-3">
          {teams.map((team, index) => (
            <div key={team.abbr} className="flex items-center gap-4 group cursor-pointer">
              <div
                className={`w-10 h-10 rounded-lg ${team.color} flex items-center justify-center text-white font-bold text-sm flex-shrink-0`}
              >
                {team.abbr}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium group-hover:text-primary transition-colors">{team.name}</span>
                  <span className="font-bold text-lg">{team.probability}%</span>
                </div>
                <div className="h-2 bg-accent rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all group-hover:bg-primary/80"
                    style={{ width: `${team.probability * 5}%` }}
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
