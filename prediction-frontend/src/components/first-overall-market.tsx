import { Card } from "@/components/ui/card"
import { TrendingUp } from "lucide-react"

const prospects = [
  { name: "James Hagens", position: "C", abbr: "JH", probability: 42, color: "bg-blue-600" },
  { name: "Porter Martone", position: "RW", abbr: "PM", probability: 28, color: "bg-red-600" },
  { name: "Matthew Schaefer", position: "D", abbr: "MS", probability: 18, color: "bg-purple-600" },
  { name: "Anton Frondell", position: "LW", abbr: "AF", probability: 8, color: "bg-green-600" },
  { name: "Michael Misa", position: "C", abbr: "MM", probability: 4, color: "bg-orange-600" },
]

export function FirstOverallMarket() {
  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-balance">First Overall Pick</h2>
        <button className="text-sm text-primary font-medium hover:underline">Show More</button>
      </div>
      <Card className="p-6">
        <div className="space-y-3">
          {prospects.map((prospect, index) => (
            <div key={prospect.name} className="flex items-center gap-4 group cursor-pointer">
              <div
                className={`w-10 h-10 rounded-lg ${prospect.color} flex items-center justify-center text-white font-bold text-xs flex-shrink-0`}
              >
                {prospect.abbr}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <div>
                    <span className="font-medium group-hover:text-primary transition-colors">{prospect.name}</span>
                    <span className="text-sm text-muted-foreground ml-2">{prospect.position}</span>
                  </div>
                  <span className="font-bold text-lg">{prospect.probability}%</span>
                </div>
                <div className="h-2 bg-accent rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all group-hover:bg-primary/80"
                    style={{ width: `${prospect.probability * 2}%` }}
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
