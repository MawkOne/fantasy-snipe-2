import Header from "@/components/header"
import DraftWizardNav from "@/components/draft-wizard-nav"
import DraftSettings from "@/components/draft-settings"

export default function DraftSettingsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-6">
          <aside>
            <DraftWizardNav active="Draft Simulator" />
          </aside>

          <main>
            <DraftSettings />
          </main>
        </div>
      </div>
    </div>
  )
}
