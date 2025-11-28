import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Search } from "lucide-react"

export default function PlayerComparisonTool() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Fantasy Hockey</CardTitle>
        <h3 className="text-xl font-bold">Who Should I Draft</h3>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input placeholder="Enter First Player" className="pl-10 bg-slate-800 text-white border-slate-700" />
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input placeholder="Enter Second Player" className="pl-10 bg-slate-800 text-white border-slate-700" />
        </div>
        <Button className="w-full bg-blue-600 hover:bg-blue-700">See Advice</Button>
      </CardContent>
    </Card>
  )
}
