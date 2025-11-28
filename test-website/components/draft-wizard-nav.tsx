import { cn } from "@/lib/utils"
import { ChevronRight } from "lucide-react"

const sections = [
  { label: "Draft Simulator" },
  { label: "Mock Draft Lobby" },
  { label: "Draft Assistant" },
  { label: "Draft Intel" },
  { label: "Cheat Sheet Creator" },
  { label: "Perfect Draft" },
  { label: "Draft Analyzer" },
  { label: "Salary Cap Simulator" },
  { label: "Salary Cap Calculator" },
]

const dynastyTools = [{ label: "Dynasty Draft Simulator" }, { label: "Rookie Draft Simulator" }]

const resources = [
  { label: "2025 Draft Kit" },
  { label: "Podcast" },
  { label: "Discord Chat" },
  { label: "Draft Wizard ADP" },
]

export default function DraftWizardNav({ active = "Draft Simulator" }: { active?: string }) {
  return (
    <nav className="rounded-lg border bg-white p-2">
      <div className="px-2 py-3 text-[11px] font-semibold uppercase text-gray-500">NHL Draft Wizard</div>
      <div className="space-y-1">
        {sections.map((s) => (
          <a
            key={s.label}
            href="#"
            className={cn(
              "flex items-center justify-between rounded-md px-3 py-2 text-sm hover:bg-gray-50",
              s.label === active ? "bg-blue-50 text-blue-700" : "text-gray-700",
            )}
          >
            <span>{s.label}</span>
            <ChevronRight className="w-4 h-4 text-gray-400" />
          </a>
        ))}
      </div>

      <div className="px-2 py-3 mt-4 text-[11px] font-semibold uppercase text-gray-500">Dynasty Tools</div>
      <div className="space-y-1">
        {dynastyTools.map((s) => (
          <a
            key={s.label}
            href="#"
            className="flex items-center justify-between rounded-md px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            <span>{s.label}</span>
            <ChevronRight className="w-4 h-4 text-gray-400" />
          </a>
        ))}
      </div>

      <div className="px-2 py-3 mt-4 text-[11px] font-semibold uppercase text-gray-500">Useful Resources</div>
      <div className="space-y-1">
        {resources.map((s) => (
          <a
            key={s.label}
            href="#"
            className="flex items-center justify-between rounded-md px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            <span>{s.label}</span>
            <ChevronRight className="w-4 h-4 text-gray-400" />
          </a>
        ))}
      </div>
    </nav>
  )
}
