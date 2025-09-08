interface PageProps {
  params: { slug: string }
}

const friendlyTitle = (slug: string) =>
  slug
    .replace(/-/g, " ")
    .replace(/\b([a-z])/g, (m) => m.toUpperCase())

export default function RankingsLanding({ params }: PageProps) {
  const t = friendlyTitle(params.slug)
  return (
    <div className="container mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-2">{t}</h1>
      <p className="text-muted-foreground">Content coming soon.</p>
    </div>
  )
}


