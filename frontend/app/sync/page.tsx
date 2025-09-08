import Header from "@/components/header"
import SyncLeague from "@/components/sync-league"

export default function SyncPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <SyncLeague />
      </main>
    </div>
  )
}
