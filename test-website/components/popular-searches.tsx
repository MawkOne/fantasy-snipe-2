import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import Link from "next/link"

export default function PopularSearches() {
  const searches = ["McDavid or Draisaitl", "MacKinnon or Pastrnak", "Ovechkin or Stamkos"]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Popular Searches</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {searches.map((search, index) => (
            <Link
              key={index}
              href={`/compare/${search.toLowerCase().replace(/\s+/g, "-")}`}
              className="block text-blue-600 hover:text-blue-800 text-sm"
            >
              {search}
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
