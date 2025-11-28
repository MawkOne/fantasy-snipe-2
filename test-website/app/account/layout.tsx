import type { ReactNode } from "react"
import AccountSidebar from "@/components/account-sidebar"

export default function AccountLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-[calc(100vh-64px)] w-full">
      <div className="mx-auto max-w-7xl px-4 md:px-6 py-6 grid grid-cols-1 md:grid-cols-[260px_minmax(0,1fr)] gap-6">
        <aside className="bg-white border rounded-lg h-full">
          <AccountSidebar />
        </aside>
        <main className="bg-white border rounded-lg">{children}</main>
      </div>
    </div>
  )
}
