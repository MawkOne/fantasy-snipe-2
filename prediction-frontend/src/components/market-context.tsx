"use client"

import { Card } from "@/components/ui/card"
import { useState } from "react"

export function MarketContext() {
  const [showMore, setShowMore] = useState(false)

  return (
    <Card className="p-6">
      <h2 className="text-xl font-bold mb-4">Forecast Details</h2>
      <div className="space-y-4">
        <div>
          <h3 className="font-semibold mb-2">Resolution Rules</h3>
          <p className="text-sm text-muted-foreground">
            This forecast will resolve to "More" if Connor McDavid scores 60 or more goals during the 2024-25 NHL
            regular season. The consensus line is set at 60 goals based on community forecasts and statistical
            projections.
          </p>
          {showMore && (
            <div className="mt-4 space-y-2 text-sm text-muted-foreground">
              <p>
                The forecast will resolve based on official NHL statistics as reported on NHL.com at the conclusion of
                the regular season. Only regular season goals count; playoff goals are excluded.
              </p>
              <p>
                If the season is shortened or cancelled, the forecast will resolve based on the final official
                statistics at the time of cancellation. All positions will be settled according to the actual outcome.
              </p>
              <p>
                This is a fantasy sports forecast market where users can take positions on player performance outcomes
                using virtual credits for entertainment and skill-building purposes.
              </p>
            </div>
          )}
          <button
            onClick={() => setShowMore(!showMore)}
            className="text-sm text-primary font-medium hover:underline mt-2"
          >
            {showMore ? "Show less" : "Show more"}
          </button>
        </div>
      </div>
    </Card>
  )
}
