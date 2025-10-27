"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export function UserBudget() {
  // In a real app, this would come from auth context
  const userBudget = 5000 // Example budget

  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div>
          <div className="text-sm text-muted-foreground mb-1">Available Balance</div>
          <div className="text-3xl font-bold text-primary">${userBudget.toLocaleString()}</div>
        </div>
        <div className="pt-4 border-t border-border">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-muted-foreground">Active Positions</span>
            <span className="font-medium">12</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Total Value</span>
            <span className="font-medium">$3,245</span>
          </div>
        </div>
        <Button variant="outline" className="w-full bg-transparent" size="sm">
          Add Funds
        </Button>
      </div>
    </Card>
  )
}
