import { Card } from "@/components/ui/card"
import { TrendingUp } from "lucide-react"

const projectionSites = [
  { name: "MoneyPuck", abbr: "MP", probability: 22, color: "bg-emerald-600" },
  { name: "Evolving Hockey", abbr: "EH", probability: 19, color: "bg-blue-600" },
  { name: "DailyFaceoff", abbr: "DF", probability: 16, color: "bg-orange-600" },
  { name: "Natural Stat Trick", abbr: "NST", probability: 13, color: "bg-purple-600" },
  { name: "Dom Luszczyszyn", abbr: "DL", probability: 11, color: "bg-cyan-600" },
  { name: "The Athletic", abbr: "ATH", probability: 8, color: "bg-red-600" },
  { name: "Hockey Reference", abbr: "HR", probability: 5, color: "bg-amber-600" },
  { name: "Dobber Hockey", abbr: "DH", probability: 4, color: "bg-indigo-600" },
  { name: "FantasyPros", abbr: "FP", probability: 2, color: "bg-pink-600" },
]

export function ProjectionSitesMarket() {
  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-balance">Most Accurate Projections</h2>
        <button className="text-sm text-primary font-medium hover:underline">Show More</button>
      </div>
      <Card className="p-6">
        <div className="space-y-3">
          {projectionSites.map((site, index) => (
            <div key={site.abbr} className="flex items-center gap-4 group cursor-pointer">
              <div
                className={`w-10 h-10 rounded-lg ${site.color} flex items-center justify-center text-white font-bold text-xs flex-shrink-0`}
              >
                {site.abbr}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium group-hover:text-primary transition-colors">{site.name}</span>
                  <span className="font-bold text-lg">{site.probability}%</span>
                </div>
                <div className="h-2 bg-accent rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all group-hover:bg-primary/80"
                    style={{ width: `${site.probability * 4}%` }}
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
