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
import { usePathname, useSearchParams } from "next/navigation"

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const pathname = usePathname()
  const searchParams = useSearchParams()

  // Get current page-specific tabs
  const getPageTabs = () => {
    if (pathname.startsWith("/players")) {
      // Extract current query params
      const currentPos = searchParams.get('pos') || ''
      const currentTimeframe = searchParams.get('timeframe') || ''
      const currentMetric = searchParams.get('metric') || ''
      
      const metricTabs = [
        { id: "Points", label: "Points", href: `/players?metric=Points${currentPos?`&pos=${currentPos}`:''}${currentTimeframe?`&timeframe=${currentTimeframe}`:''}` },
        { id: "Goals", label: "Goals", href: `/players?metric=Goals${currentPos?`&pos=${currentPos}`:''}${currentTimeframe?`&timeframe=${currentTimeframe}`:''}` },
        { id: "Assists", label: "Assists", href: `/players?metric=Assists${currentPos?`&pos=${currentPos}`:''}${currentTimeframe?`&timeframe=${currentTimeframe}`:''}` },
      ]
      
      const positionTabs = [
        { id: "F", label: "Forwards", href: `/players?${currentMetric?`metric=${currentMetric}&`:''}pos=F${currentTimeframe?`&timeframe=${currentTimeframe}`:''}` },
        { id: "D", label: "Defence", href: `/players?${currentMetric?`metric=${currentMetric}&`:''}pos=D${currentTimeframe?`&timeframe=${currentTimeframe}`:''}` },
        { id: "G", label: "Goalies", href: `/players?${currentMetric?`metric=${currentMetric}&`:''}pos=G${currentTimeframe?`&timeframe=${currentTimeframe}`:''}` },
      ]
      
      const timeframeTabs = [
        { id: "Season", label: "Season", href: `/players?${currentMetric?`metric=${currentMetric}&`:''}${currentPos?`pos=${currentPos}&`:''}timeframe=Season` },
        { id: "Monthly", label: "Monthly", href: `/players?${currentMetric?`metric=${currentMetric}&`:''}${currentPos?`pos=${currentPos}&`:''}timeframe=Monthly` },
        { id: "Weekly", label: "Weekly", href: `/players?${currentMetric?`metric=${currentMetric}&`:''}${currentPos?`pos=${currentPos}&`:''}timeframe=Weekly` },
      ]
      
      return {
        tabs: [...metricTabs, ...positionTabs, ...timeframeTabs],
        activeMetric: currentMetric || '',
        activePos: currentPos || '',
        activeTimeframe: currentTimeframe || ''
      }
    }
    
    if (pathname.startsWith("/teams")) {
      return {
        tabs: [
          { id: "standings", label: "Standings", href: "/teams?view=standings" },
          { id: "playoffs", label: "Playoffs", href: "/teams?view=playoffs" },
          { id: "awards", label: "Awards", href: "/teams?view=awards" },
        ],
        activeMetric: '',
        activePos: '',
        activeTimeframe: ''
      }
    }
    
    if (pathname.startsWith("/trades")) {
      return {
        tabs: [
          { id: "recent", label: "Recent", href: "/trades?view=recent" },
          { id: "mine", label: "My Trades", href: "/trades?view=mine" },
          { id: "leaderboard", label: "Leaderboard", href: "/trades?view=leaderboard" },
        ],
        activeMetric: '',
        activePos: '',
        activeTimeframe: ''
      }
    }
    
    return { tabs: [], activeMetric: '', activePos: '', activeTimeframe: '' }
  }

  const { tabs: pageTabs, activeMetric, activePos, activeTimeframe } = getPageTabs()

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
              {/* Markets Dropdown */}
              <div className="relative group">
                <button className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground">
                  Markets <ChevronDown className="w-3 h-3" />
                </button>
                <div className="absolute left-0 top-full mt-2 w-48 bg-popover border border-border rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                  <div className="py-1">
                    <Link href="/players" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      Players
                    </Link>
                    <Link href="/teams" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      Teams
                    </Link>
                    <Link href="/trades" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      Trades
                    </Link>
                  </div>
                </div>
              </div>

              {/* Leagues Dropdown */}
              <div className="relative group">
                <button className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground">
                  Leagues <ChevronDown className="w-3 h-3" />
                </button>
                <div className="absolute left-0 top-full mt-2 w-48 bg-popover border border-border rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                  <div className="py-1">
                    <Link href="/leagues/create" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      Create League
                    </Link>
                    <Link href="/leagues/join" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      Join League
                    </Link>
                    <Link href="/leagues/my-leagues" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      My Leagues
                    </Link>
                  </div>
                </div>
              </div>

              {/* Tools Dropdown */}
              <div className="relative group">
                <button className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground">
                  Tools <ChevronDown className="w-3 h-3" />
                </button>
                <div className="absolute left-0 top-full mt-2 w-48 bg-popover border border-border rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                  <div className="py-1">
                    <Link href="/tools/lineup-optimizer" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      Lineup Optimizer
                    </Link>
                    <Link href="/tools/trade-analyzer" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      Trade Analyzer
                    </Link>
                    <Link href="/tools/waiver-assistant" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      Waiver Assistant
                    </Link>
                  </div>
                </div>
              </div>

              {/* Research Dropdown */}
              <div className="relative group">
                <button className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground">
                  Research <ChevronDown className="w-3 h-3" />
                </button>
                <div className="absolute left-0 top-full mt-2 w-48 bg-popover border border-border rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                  <div className="py-1">
                    <Link href="/research/player-stats" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      Player Stats
                    </Link>
                    <Link href="/research/team-analytics" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      Team Analytics
                    </Link>
                    <Link href="/research/injury-reports" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      Injury Reports
                    </Link>
                  </div>
                </div>
              </div>

              {/* Resources Dropdown */}
              <div className="relative group">
                <button className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground">
                  Resources <ChevronDown className="w-3 h-3" />
                </button>
                <div className="absolute left-0 top-full mt-2 w-48 bg-popover border border-border rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                  <div className="py-1">
                    <Link href="/resources/guides" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      Guides
                    </Link>
                    <Link href="/resources/tutorials" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      Tutorials
                    </Link>
                    <Link href="/resources/faq" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      FAQ
                    </Link>
                    <div className="border-t border-border my-1"></div>
                    <Link href="/community" className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground">
                      Community
                    </Link>
                  </div>
                </div>
              </div>
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

        {pathname.startsWith("/players") && (
          <div className="border-t border-border py-3">
            <div className="flex gap-3 items-center">
              <DropdownMenu>
                <DropdownMenuTrigger className="px-4 py-2 rounded-lg font-medium text-sm bg-primary text-primary-foreground flex items-center gap-1">
                  {activeMetric || "Points"} <ChevronDown className="w-3 h-3" />
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem asChild>
                    <Link href={`/players?metric=Points${searchParams.get('pos')?`&pos=${searchParams.get('pos')}`:''}${searchParams.get('timeframe')?`&timeframe=${searchParams.get('timeframe')}`:''}`}>Points</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href={`/players?metric=Goals${searchParams.get('pos')?`&pos=${searchParams.get('pos')}`:''}${searchParams.get('timeframe')?`&timeframe=${searchParams.get('timeframe')}`:''}`}>Goals</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href={`/players?metric=Assists${searchParams.get('pos')?`&pos=${searchParams.get('pos')}`:''}${searchParams.get('timeframe')?`&timeframe=${searchParams.get('timeframe')}`:''}`}>Assists</Link>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <DropdownMenu>
                <DropdownMenuTrigger className="px-4 py-2 rounded-lg font-medium text-sm bg-accent text-accent-foreground hover:bg-accent/80 flex items-center gap-1">
                  {activePos === "F" ? "Forwards" : activePos === "D" ? "Defence" : activePos === "G" ? "Goalies" : "All Positions"} <ChevronDown className="w-3 h-3" />
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem asChild>
                    <Link href={`/players?${searchParams.get('metric')?`metric=${searchParams.get('metric')}&`:''}pos=F${searchParams.get('timeframe')?`&timeframe=${searchParams.get('timeframe')}`:''}`}>Forwards</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href={`/players?${searchParams.get('metric')?`metric=${searchParams.get('metric')}&`:''}pos=D${searchParams.get('timeframe')?`&timeframe=${searchParams.get('timeframe')}`:''}`}>Defence</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href={`/players?${searchParams.get('metric')?`metric=${searchParams.get('metric')}&`:''}pos=G${searchParams.get('timeframe')?`&timeframe=${searchParams.get('timeframe')}`:''}`}>Goalies</Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link href={`/players?${searchParams.get('metric')?`metric=${searchParams.get('metric')}`:''}${searchParams.get('timeframe')?`&timeframe=${searchParams.get('timeframe')}`:''}`}>All Positions</Link>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <DropdownMenu>
                <DropdownMenuTrigger className="px-4 py-2 rounded-lg font-medium text-sm bg-accent text-accent-foreground hover:bg-accent/80 flex items-center gap-1">
                  {activeTimeframe || "All Timeframes"} <ChevronDown className="w-3 h-3" />
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem asChild>
                    <Link href={`/players?${searchParams.get('metric')?`metric=${searchParams.get('metric')}&`:''}${searchParams.get('pos')?`pos=${searchParams.get('pos')}&`:''}timeframe=Season`}>Season</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href={`/players?${searchParams.get('metric')?`metric=${searchParams.get('metric')}&`:''}${searchParams.get('pos')?`pos=${searchParams.get('pos')}&`:''}timeframe=Monthly`}>Monthly</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href={`/players?${searchParams.get('metric')?`metric=${searchParams.get('metric')}&`:''}${searchParams.get('pos')?`pos=${searchParams.get('pos')}&`:''}timeframe=Weekly`}>Weekly</Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link href={`/players?${searchParams.get('metric')?`metric=${searchParams.get('metric')}`:''}${searchParams.get('pos')?`&pos=${searchParams.get('pos')}`:''}`}>All Timeframes</Link>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        )}

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
