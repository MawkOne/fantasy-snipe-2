import { Card } from "@/components/ui/card"

const accuracyMarkets = [
  {
    title: "Goals Leader Accuracy",
    sites: [
      { name: "MoneyPuck", abbr: "MP", probability: 28 },
      { name: "Evolving Hockey", abbr: "EH", probability: 22 },
      { name: "DailyFaceoff", abbr: "DF", probability: 18 },
      { name: "Dom Luszczyszyn", abbr: "DL", probability: 15 },
      { name: "The Athletic", abbr: "ATH", probability: 12 },
    ],
  },
  {
    title: "Points Leader Accuracy",
    sites: [
      { name: "Evolving Hockey", abbr: "EH", probability: 30 },
      { name: "MoneyPuck", abbr: "MP", probability: 25 },
      { name: "Dom Luszczyszyn", abbr: "DL", probability: 20 },
      { name: "Natural Stat Trick", abbr: "NST", probability: 15 },
      { name: "DailyFaceoff", abbr: "DF", probability: 10 },
    ],
  },
  {
    title: "Team Standings Accuracy",
    sites: [
      { name: "MoneyPuck", abbr: "MP", probability: 35 },
      { name: "Evolving Hockey", abbr: "EH", probability: 28 },
      { name: "Dom Luszczyszyn", abbr: "DL", probability: 18 },
      { name: "The Athletic", abbr: "ATH", probability: 12 },
      { name: "Hockey Reference", abbr: "HR", probability: 7 },
    ],
  },
]

export function ProjectionAccuracyGrid() {
  return (
    <section>
      <h2 className="text-2xl font-bold mb-4 text-balance">Category Accuracy Markets</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {accuracyMarkets.map((market) => (
          <Card key={market.title} className="p-6">
            <h3 className="font-bold text-lg mb-4">{market.title}</h3>
            <div className="space-y-3">
              {market.sites.map((site, index) => (
                <div key={site.abbr} className="group cursor-pointer">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm group-hover:text-primary transition-colors truncate">
                        {site.name}
                      </div>
                      <div className="text-xs text-muted-foreground">{site.abbr}</div>
                    </div>
                    <div className="font-bold ml-2">{site.probability}%</div>
                  </div>
                  {index < market.sites.length - 1 && <div className="h-px bg-border mt-3" />}
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </section>
  )
}
