import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function DraftPicksPage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Draft Picks</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">
            Track and manage your league&apos;s draft picks here. This is a placeholder; wire real picks data next.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
