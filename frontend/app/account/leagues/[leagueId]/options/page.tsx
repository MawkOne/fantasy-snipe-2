"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function OptionsPage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Options</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button variant="outline" className="bg-transparent w-full" onClick={() => alert("Export settings")}>
            Export League Settings
          </Button>
          <Button variant="destructive" className="w-full" onClick={() => alert("Disconnect league")}>
            Disconnect League
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
