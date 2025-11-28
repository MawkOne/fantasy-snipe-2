import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Image from "next/image"
import Link from "next/link"

export default function LatestArticles() {
  const categories = ["Featured", "NHL", "Fantasy", "DFS", "Premium"]

  const articles = [
    {
      title: "Top 10 Sleeper Picks for 2025 Fantasy Hockey",
      image: "/hockey-sleeper-picks-cover.png",
      category: "NHL",
    },
    {
      title: "Dynasty League Strategy Guide",
      image: "/dynasty-hockey-cover.png",
      category: "Fantasy",
    },
    {
      title: "DFS Lineup Optimizer Tips",
      image: "/hockey-dfs-optimizer-cover.png",
      category: "DFS",
    },
  ]

  return (
    <section aria-labelledby="latest-articles-heading">
      <div className="flex items-center justify-between mb-5">
        <h2 id="latest-articles-heading" className="text-2xl font-bold">
          Latest Articles
        </h2>
        <Link href="/articles" className="text-blue-600 hover:text-blue-800 text-sm font-medium">
          View All
        </Link>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-6">
        {categories.map((category) => {
          const active = category === "Featured"
          return (
            <Button
              key={category}
              variant={active ? "default" : "outline"}
              size="sm"
              className={
                active ? "bg-blue-600 hover:bg-blue-700" : "bg-white hover:bg-gray-50 text-gray-700 border-gray-300"
              }
            >
              {category}
            </Button>
          )
        })}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {articles.map((article, index) => (
          <Card key={index} className="overflow-hidden rounded-xl hover:shadow-md transition-shadow">
            <div className="relative h-44">
              <Image src={article.image || "/placeholder.svg"} alt={article.title} fill className="object-cover" />
            </div>
            <CardContent className="p-4">
              <span className="text-xs text-blue-600 font-semibold uppercase tracking-wide">{article.category}</span>
              <h3 className="font-semibold mt-2 line-clamp-2">{article.title}</h3>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  )
}
