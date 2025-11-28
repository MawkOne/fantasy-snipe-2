import PlaybookSidebar from "@/components/playbook-sidebar"
import PlaybookDashboard from "@/components/playbook-dashboard"

export default function MyPlaybookPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        <PlaybookSidebar />
        <main className="flex-1">
          <PlaybookDashboard />
        </main>
      </div>
    </div>
  )
}
