import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function MockDraftsPage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Mock Drafts</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-gray-600">Run mock drafts using your league settings to practice strategy.</p>
          <a href="/draft-wizard/mock-draft-simulator">
            <Button className="bg-blue-600 hover:bg-blue-700">Start a Mock</Button>
          </a>
        </CardContent>
      </Card>
    </div>
  )
}
