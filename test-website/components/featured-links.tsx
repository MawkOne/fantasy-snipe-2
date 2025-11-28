import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import Link from "next/link"

export default function FeaturedLinks() {
  const links = [
    "2025 Half-PPR Draft Rankings",
    "PPR Draft Rankings",
    "Dynasty Rankings",
    "Half-PPR Cheatsheet",
    "Sleeper Rankings",
    "PPR Cheatsheet",
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Featured Links</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {links.map((link, index) => (
            <Link
              key={index}
              href={`/${link.toLowerCase().replace(/\s+/g, "-")}`}
              className="block text-gray-700 hover:text-blue-600 text-sm border-b border-gray-200 pb-2"
            >
              {link}
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
