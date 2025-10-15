import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface MultiOptionOutcome {
  id: string
  name: string
  team?: string
  probability: number
  buyPrice: number
  sellPrice: number
  volume: string
  image?: string
}

interface MultiOptionOutcomesProps {
  outcomes: MultiOptionOutcome[]
}

export function MultiOptionOutcomes({ outcomes }: MultiOptionOutcomesProps) {
  return (
    <Card className="p-4 sm:p-6">
      <div className="space-y-2">
        {outcomes.map((outcome, index) => (
          <div
            key={outcome.id}
            className="flex items-center justify-between gap-3 sm:gap-4 p-3 sm:p-4 rounded-lg border border-border hover:bg-accent/30 transition-colors"
          >
            <div className="flex items-center gap-3 flex-1 min-w-0">
              {outcome.image && (
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full overflow-hidden border border-border/50 flex-shrink-0">
                  <img
                    src={outcome.image || "/placeholder.svg"}
                    alt={outcome.name}
                    className="w-full h-full object-cover"
                  />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-sm sm:text-base truncate">{outcome.name}</div>
                {outcome.team && <div className="text-xs text-muted-foreground">{outcome.team}</div>}
              </div>
              <div className="text-xl sm:text-2xl font-bold text-primary flex-shrink-0">{outcome.probability}%</div>
            </div>
            <div className="flex gap-2 flex-shrink-0">
              <Button
                size="sm"
                className="bg-green-600 hover:bg-green-700 text-white min-w-16 sm:min-w-20 text-xs sm:text-sm"
              >
                ${outcome.buyPrice}IM
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="border-red-600 text-red-600 hover:bg-red-50 min-w-16 sm:min-w-20 bg-transparent text-xs sm:text-sm"
              >
                ${outcome.sellPrice}IM
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
