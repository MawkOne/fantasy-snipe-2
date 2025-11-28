"use client"

import { useState } from "react"
import Link from "next/link"
import { Card, CardContent } from "@/components/ui/card"
import {
  ChevronDown,
  ChevronRight,
  Users,
  TrendingUp,
  ArrowUpDown,
  Lock,
  FolderSyncIcon as Sync,
  Home,
} from "lucide-react"
import { cn } from "@/lib/utils"

export default function PlaybookSidebar() {
  const [expandedSections, setExpandedSections] = useState<string[]>(["lineup"])

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => (prev.includes(section) ? prev.filter((s) => s !== section) : [...prev, section]))
  }

  const menuSections = [
    {
      id: "sync",
      title: "SYNC A League",
      subtitle: "Free Sync",
      icon: Sync,
      items: [],
    },
    {
      id: "dashboard",
      title: "Dashboard",
      icon: Home,
      items: [],
      active: true,
    },
    {
      id: "lineup",
      title: "Lineup",
      icon: Users,
      items: [
        { name: "My Team", href: "/my-playbook/my-team" },
        { name: "Matchup", href: "/my-playbook/matchup" },
        { name: "Who Should I Start", href: "/my-playbook/who-should-i-start", external: true },
        { name: "Start/Sit Assistant", href: "/my-playbook/start-sit", premium: true },
        { name: "Auto-Pilot", href: "/my-playbook/auto-pilot", premium: true },
        { name: "My Primer", href: "/my-playbook/primer" },
        { name: "Are They Playing", href: "/my-playbook/playing-status" },
      ],
    },
    {
      id: "waiver",
      title: "Waiver",
      icon: TrendingUp,
      items: [
        { name: "Top Available", href: "/my-playbook/top-available" },
        { name: "Waiver Central", href: "/my-playbook/waiver-central" },
        { name: "Cheat Sheets", href: "/my-playbook/cheat-sheets" },
        { name: "Waiver Assistant", href: "/my-playbook/waiver-assistant", premium: true },
        { name: "Free Agent Finder", href: "/my-playbook/free-agents", premium: true },
      ],
    },
    {
      id: "trade",
      title: "Trade",
      icon: ArrowUpDown,
      items: [
        { name: "Top Taken", href: "/my-playbook/top-taken" },
        { name: "Cheat Sheets", href: "/my-playbook/trade-cheat-sheets" },
        { name: "Trade Central", href: "/my-playbook/trade-central" },
        { name: "Trade Analyzer", href: "/my-playbook/trade-analyzer", premium: true },
        { name: "Trade Finder", href: "/my-playbook/trade-finder", premium: true },
      ],
    },
  ]

  return (
    <aside className="w-80 bg-white border-r border-gray-200 min-h-screen">
      <div className="p-4">
        {menuSections.map((section) => (
          <div key={section.id} className="mb-2">
            {section.id === "sync" ? (
              <Link href="/sync">
                <Card className="mb-4 bg-blue-50 border-blue-200 hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center space-x-3">
                      <div className="bg-blue-600 rounded-lg p-2">
                        <section.icon className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-blue-900">{section.title}</h3>
                        <p className="text-sm text-blue-700">{section.subtitle}</p>
                      </div>
                      <ChevronDown className="w-4 h-4 text-blue-600 ml-auto" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ) : section.items.length === 0 ? (
              <Link href="/my-playbook">
                <div
                  className={cn(
                    "flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-100 transition-colors",
                    section.active && "bg-blue-50 text-blue-700 border-l-4 border-blue-600",
                  )}
                >
                  <section.icon className="w-5 h-5" />
                  <span className="font-medium">{section.title}</span>
                </div>
              </Link>
            ) : (
              <div>
                <button
                  onClick={() => toggleSection(section.id)}
                  className="flex items-center space-x-3 p-3 w-full text-left hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <section.icon className="w-5 h-5" />
                  <span className="font-medium">{section.title}</span>
                  {expandedSections.includes(section.id) ? (
                    <ChevronDown className="w-4 h-4 ml-auto" />
                  ) : (
                    <ChevronRight className="w-4 h-4 ml-auto" />
                  )}
                </button>

                {expandedSections.includes(section.id) && (
                  <div className="ml-8 space-y-1">
                    {section.items.map((item) => (
                      <Link
                        key={item.name}
                        href={item.href}
                        className="flex items-center justify-between p-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded transition-colors"
                      >
                        <span>{item.name}</span>
                        <div className="flex items-center space-x-1">
                          {item.external && <span className="text-xs text-blue-600">↗</span>}
                          {item.premium && <Lock className="w-3 h-3 text-orange-500" />}
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </aside>
  )
}
