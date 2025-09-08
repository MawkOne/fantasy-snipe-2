import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function KeepersPage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Keepers</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-gray-600">
            Assign and manage keeper players for this season. Add rules for costs and limits.
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary" className="bg-gray-100 text-gray-800">
              Max keepers: 3
            </Badge>
            <Badge variant="secondary" className="bg-gray-100 text-gray-800">
              Keeper cost: Draft Round +1
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
