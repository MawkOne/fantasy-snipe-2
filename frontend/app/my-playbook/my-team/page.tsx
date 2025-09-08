import Header from "@/components/header"
import PlaybookSidebar from "@/components/playbook-sidebar"
import MyTeamContent from "@/components/my-team-content"

export default function MyTeamPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <PlaybookSidebar />
        <main className="flex-1">
          <MyTeamContent />
        </main>
      </div>
    </div>
  )
}
