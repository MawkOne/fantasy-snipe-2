import Link from "next/link"
import { Home, Users, BarChart3, FileText, Settings, Trophy, Target, Calendar } from "lucide-react"

export default function Sidebar() {
  const menuItems = [
    { icon: Home, label: "Home", href: "/" },
    { icon: Trophy, label: "NHL", href: "/nhl" },
    { icon: Users, label: "My League", href: "/league" },
    { icon: Target, label: "Draft", href: "/draft" },
    { icon: BarChart3, label: "Rankings", href: "/rankings" },
    { icon: FileText, label: "Cheat Sheet", href: "/cheat-sheet" },
    { icon: Calendar, label: "Schedule", href: "/schedule" },
    { icon: Settings, label: "Tools", href: "/tools" },
  ]

  return (
    <aside className="w-16 bg-slate-900 min-h-screen">
      <div className="flex flex-col items-center py-4 space-y-4">
        {menuItems.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className="flex flex-col items-center p-2 text-gray-400 hover:text-orange-400 transition-colors group"
          >
            <item.icon className="w-6 h-6 mb-1" />
            <span className="text-xs text-center">{item.label}</span>
          </Link>
        ))}
      </div>
    </aside>
  )
}
