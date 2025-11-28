interface ComparePageProps {
  params: { slug: string }
}

export default function ComparePage({ params }: ComparePageProps) {
  const title = params.slug
    .replace(/-/g, " ")
    .replace(/\bor\b/g, "vs.")
    .replace(/\b([a-z])/g, (m) => m.toUpperCase())

  return (
    <div className="container mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-2">Player Comparison</h1>
      <p className="text-muted-foreground mb-6">{title}</p>
      <p className="text-sm text-muted-foreground">Comparison tool coming soon.</p>
    </div>
  )
}


