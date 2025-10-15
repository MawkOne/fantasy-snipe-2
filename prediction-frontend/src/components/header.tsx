"use client"

import { Menu, X, ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import Link from "next/link"
import { useState } from "react"
import { usePathname } from "next/navigation"

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const pathname = usePathname()

  const getActiveTab = () => {
    if (pathname === "/") return "teams"
    if (pathname.startsWith("/players")) return "players"
    if (pathname.startsWith("/trades")) return "trades"
    if (pathname.startsWith("/projections")) return "projections"
    if (pathname.startsWith("/awards")) return "awards"
    if (pathname.startsWith("/draft")) return "draft"
    return "teams"
  }

  const activeTab = getActiveTab()
  const activeTimeframe = "season"

  const marketTabs = [
    { id: "teams", label: "Teams", href: "/" },
    { id: "players", label: "Players", href: "/players" },
    { id: "trades", label: "Trades", href: "/trades" },
    { id: "projections", label: "Projections", href: "/projections" },
    { id: "awards", label: "Awards", href: "/awards" },
    { id: "draft", label: "Draft", href: "/draft" },
  ]

  const timeframes = [
    { id: "season", label: "Season" },
    { id: "monthly", label: "Monthly" },
    { id: "weekly", label: "Weekly" },
  ]

  return (
    <header className="border-b border-border bg-card sticky top-0 z-50">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-4 md:gap-8">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-lg">🏒</span>
              </div>
              <span className="font-bold text-lg md:text-xl">IceMarkets</span>
            </Link>
            <nav className="hidden lg:flex items-center gap-6">
              <DropdownMenu>
                <DropdownMenuTrigger className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground">
                  Leagues <ChevronDown className="w-3 h-3" />
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem asChild>
                    <Link href="/leagues/create">Create League</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/leagues/join">Join League</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/leagues/my-leagues">My Leagues</Link>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <DropdownMenu>
                <DropdownMenuTrigger className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground">
                  Tools <ChevronDown className="w-3 h-3" />
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem asChild>
                    <Link href="/tools/lineup-optimizer">Lineup Optimizer</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/tools/trade-analyzer">Trade Analyzer</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/tools/waiver-assistant">Waiver Assistant</Link>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <DropdownMenu>
                <DropdownMenuTrigger className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground">
                  Research <ChevronDown className="w-3 h-3" />
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem asChild>
                    <Link href="/research/player-stats">Player Stats</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/research/team-analytics">Team Analytics</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/research/injury-reports">Injury Reports</Link>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <DropdownMenu>
                <DropdownMenuTrigger className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground">
                  Resources <ChevronDown className="w-3 h-3" />
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem asChild>
                    <Link href="/resources/guides">Guides</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/resources/tutorials">Tutorials</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/resources/faq">FAQ</Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link href="/community">Community</Link>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </nav>
          </div>
          <div className="flex items-center gap-2 md:gap-4">
            <Button variant="outline" size="sm" className="hidden sm:flex bg-transparent" asChild>
              <Link href="/login">Log In</Link>
            </Button>
            <Button size="sm" asChild>
              <Link href="/signup" className="text-xs sm:text-sm">
                Get Started
              </Link>
            </Button>
            <button
              className="lg:hidden p-2 hover:bg-accent rounded-lg"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        <div className="border-t border-border py-3">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
              {marketTabs.map((tab) => (
                <Link
                  key={tab.id}
                  href={tab.href}
                  className={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap text-sm ${
                    activeTab === tab.id
                      ? "bg-primary text-primary-foreground"
                      : "bg-accent text-accent-foreground hover:bg-accent/80"
                  }`}
                >
                  {tab.label}
                </Link>
              ))}
            </div>

            <div className="flex gap-2 flex-shrink-0 overflow-x-auto pb-2 scrollbar-hide">
              {timeframes.map((timeframe) => (
                <button
                  key={timeframe.id}
                  className={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap text-sm ${
                    activeTimeframe === timeframe.id
                      ? "bg-primary text-primary-foreground"
                      : "bg-accent text-accent-foreground hover:bg-accent/80"
                  }`}
                >
                  {timeframe.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {mobileMenuOpen && (
          <nav className="lg:hidden border-t border-border py-4 space-y-2">
            <Link
              href="/leagues"
              className="block px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg"
              onClick={() => setMobileMenuOpen(false)}
            >
              Leagues
            </Link>
            <Link
              href="/tools"
              className="block px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg"
              onClick={() => setMobileMenuOpen(false)}
            >
              Tools
            </Link>
            <Link
              href="/research"
              className="block px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg"
              onClick={() => setMobileMenuOpen(false)}
            >
              Research
            </Link>
            <Link
              href="/resources"
              className="block px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg"
              onClick={() => setMobileMenuOpen(false)}
            >
              Resources
            </Link>
            <div className="sm:hidden px-4 pt-2">
              <Button variant="outline" size="sm" className="w-full mb-2 bg-transparent" asChild>
                <Link href="/login">Log In</Link>
              </Button>
            </div>
          </nav>
        )}
      </div>
    </header>
  )
}
