import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"

export default function RankingsFilters() {
  const positions = ["Overall", "C", "LW", "RW", "D", "G", "Util", "More"]

  return (
    <div className="space-y-4 mb-6">
      {/* Filter Controls */}
      <div className="flex flex-wrap items-center gap-4 p-4 bg-white rounded-lg border">
        <div className="flex items-center space-x-2">
          <Label htmlFor="rankings-type">Rankings</Label>
          <Select defaultValue="draft">
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="weekly">Weekly</SelectItem>
              <SelectItem value="ros">ROS</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center space-x-2">
          <Label htmlFor="scoring">Scoring</Label>
          <Select defaultValue="standard">
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="standard">Standard</SelectItem>
              <SelectItem value="points">Points</SelectItem>
              <SelectItem value="categories">Categories</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center space-x-2">
          <Label htmlFor="view">View</Label>
          <Select defaultValue="overview">
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="overview">Overview</SelectItem>
              <SelectItem value="detailed">Detailed</SelectItem>
              <SelectItem value="projections">Projections</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center space-x-2">
          <Label htmlFor="experts">Experts</Label>
          <Select defaultValue="latest">
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="latest">Latest ECR</SelectItem>
              <SelectItem value="all">All Experts</SelectItem>
              <SelectItem value="top10">Top 10</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center space-x-2">
          <Switch id="draft-mode" />
          <Label htmlFor="draft-mode">Draft Mode</Label>
        </div>
      </div>

      {/* Position Tabs */}
      <div className="flex flex-wrap gap-2">
        {positions.map((position, index) => (
          <Button
            key={position}
            variant={index === 0 ? "default" : "outline"}
            size="sm"
            className={index === 0 ? "bg-blue-600 hover:bg-blue-700" : ""}
          >
            {position}
          </Button>
        ))}
      </div>
    </div>
  )
}
