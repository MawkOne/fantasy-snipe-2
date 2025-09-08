"use client"

import { DialogFooter } from "@/components/ui/dialog"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
  DialogClose,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import type { League } from "./league-row"
import { cn } from "@/lib/utils"

type Props = {
  league: League
  trigger: React.ReactNode
}

type Section = "Basic" | "Roster" | "Scoring" | "Draft Details" | "Draft Order"

function SectionNav({
  active,
  onChange,
}: {
  active: Section
  onChange: (s: Section) => void
}) {
  const items: Section[] = ["Basic", "Roster", "Scoring", "Draft Details", "Draft Order"]
  return (
    <nav className="md:w-[180px] md:pr-3 md:border-r md:border-border">
      {items.map((it) => (
        <NavItem key={it} label={it} active={active === it} onClick={() => onChange(it)} />
      ))}
    </nav>
  )
}

function NavItem({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full px-2.5 py-1.5 rounded-md text-left text-[13px] font-medium whitespace-nowrap md:block",
        active ? "bg-blue-50 text-blue-700 ring-1 ring-blue-200" : "text-gray-800 hover:bg-gray-100",
      )}
    >
      {label}
    </button>
  )
}

function Stepper({
  value,
  onChange,
  min = 0,
  max = 99,
}: {
  value: number
  onChange: (v: number) => void
  min?: number
  max?: number
}) {
  return (
    <div className="inline-flex items-center gap-2">
      <Button
        type="button"
        variant="outline"
        size="icon"
        onClick={() => onChange(Math.max(min, value - 1))}
        aria-label="Decrease"
      >
        {"-"}
      </Button>
      <div className="w-6 text-center tabular-nums">{value}</div>
      <Button
        type="button"
        variant="outline"
        size="icon"
        onClick={() => onChange(Math.min(max, value + 1))}
        aria-label="Increase"
      >
        {"+"}
      </Button>
    </div>
  )
}

export default function SettingsDialog({ league, trigger }: Props) {
  const [open, setOpen] = useState(false)
  const [section, setSection] = useState<Section>("Basic")

  // Mock settings state
  const [leagueType, setLeagueType] = useState("Keeper")
  const [status, setStatus] = useState("Upcoming Draft")
  const [numTeams, setNumTeams] = useState(12)
  const [playoffTeams, setPlayoffTeams] = useState(6)

  const [qb, setQb] = useState(1)
  const [rb, setRb] = useState(2)
  const [wr, setWr] = useState(3)
  const [te, setTe] = useState(1)
  const [flex, setFlex] = useState(1)
  const [bn, setBn] = useState(5)

  const [scoringPreset, setScoringPreset] = useState("Custom")
  const [passTd, setPassTd] = useState(6)
  const [passYardsPoints, setPassYardsPoints] = useState(1)
  const [passYardsPer, setPassYardsPer] = useState(25)
  const [interception, setInterception] = useState(-2)

  const [draftType, setDraftType] = useState("Snake")
  const [rounds, setRounds] = useState(15)
  const [draftDate, setDraftDate] = useState("2025-08-28")
  const [draftTime, setDraftTime] = useState("20:00")
  const [defaultRanks, setDefaultRanks] = useState("Most Accurate Experts")

  function save() {
    // Here you would call a server action or API to persist settings.
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-w-[2400px] w-[98vw] md:rounded-xl p-0 overflow-hidden" aria-describedby={undefined}>
        <div className="flex flex-col">
          <DialogHeader className="px-6 pt-6">
            <DialogTitle>Settings</DialogTitle>
            <DialogDescription>
              {league.name} — {league.teamName} • {league.provider}
            </DialogDescription>
          </DialogHeader>
          <Separator className="mt-4" />
          <div className="flex flex-col md:flex-row gap-6 px-4 md:px-5 py-6">
            <SectionNav active={section} onChange={setSection} />
            <div className="flex-1 min-w-0">
              {section === "Basic" && (
                <div className="space-y-6">
                  <div className="grid gap-2">
                    <Label>League Type</Label>
                    <Select value={leagueType} onValueChange={setLeagueType}>
                      <SelectTrigger className="max-w-sm">
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Redraft">Redraft</SelectItem>
                        <SelectItem value="Keeper">Keeper</SelectItem>
                        <SelectItem value="Dynasty">Dynasty</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid gap-2">
                    <Label>Status</Label>
                    <Select value={status} onValueChange={setStatus}>
                      <SelectTrigger className="max-w-sm">
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Upcoming Draft">Upcoming Draft</SelectItem>
                        <SelectItem value="In Season">In Season</SelectItem>
                        <SelectItem value="Offseason">Offseason</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid gap-2 max-w-md">
                    <Label>Number of Teams</Label>
                    <Stepper value={numTeams} onChange={setNumTeams} min={2} max={20} />
                  </div>

                  <div className="grid gap-2 max-w-md">
                    <Label>Playoff Teams</Label>
                    <Stepper value={playoffTeams} onChange={setPlayoffTeams} min={2} max={numTeams} />
                  </div>
                </div>
              )}

              {section === "Roster" && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4">
                    <div className="flex items-center justify-between">
                      <Label className="mr-4">QB</Label>
                      <Stepper value={qb} onChange={setQb} min={0} max={3} />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label className="mr-4">RB</Label>
                      <Stepper value={rb} onChange={setRb} min={0} max={6} />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label className="mr-4">WR</Label>
                      <Stepper value={wr} onChange={setWr} min={0} max={6} />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label className="mr-4">TE</Label>
                      <Stepper value={te} onChange={setTe} min={0} max={3} />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label className="mr-4">FLEX</Label>
                      <Stepper value={flex} onChange={setFlex} min={0} max={4} />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label className="mr-4">BN</Label>
                      <Stepper value={bn} onChange={setBn} min={0} max={15} />
                    </div>
                  </div>

                  <Separator />
                  <div>
                    <h4 className="text-lg font-semibold">IDP Positions</h4>
                    <p className="text-sm text-gray-500">Configure individual defensive player slots.</p>
                    <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4">
                      <div className="flex items-center justify-between">
                        <Label className="mr-4">DL</Label>
                        <Stepper value={0} onChange={() => {}} />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label className="mr-4">DB</Label>
                        <Stepper value={0} onChange={() => {}} />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label className="mr-4">DE</Label>
                        <Stepper value={0} onChange={() => {}} />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label className="mr-4">DT</Label>
                        <Stepper value={0} onChange={() => {}} />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {section === "Scoring" && (
                <div className="space-y-6">
                  <div className="grid gap-2 max-w-sm">
                    <Label>Scoring</Label>
                    <Select value={scoringPreset} onValueChange={setScoringPreset}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select preset" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Standard">Standard</SelectItem>
                        <SelectItem value="Half PPR">Half PPR</SelectItem>
                        <SelectItem value="PPR">PPR</SelectItem>
                        <SelectItem value="Custom">Custom</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex flex-wrap gap-4 text-sm">
                    <Button variant="secondary" className="font-semibold">
                      Passing
                    </Button>
                    <Button variant="ghost">Rushing</Button>
                    <Button variant="ghost">Receiving</Button>
                    <Button variant="ghost">IDP</Button>
                    <Button variant="ghost">Other</Button>
                  </div>

                  <div className="grid gap-4 max-w-xl">
                    <div className="grid grid-cols-3 items-center gap-3">
                      <Label className="col-span-2">Pass TD</Label>
                      <Input type="number" value={passTd} onChange={(e) => setPassTd(Number(e.target.value))} />
                    </div>

                    <div className="grid grid-cols-3 items-center gap-3">
                      <Label className="col-span-2">Passing Yards</Label>
                      <div className="flex items-center gap-2">
                        <Input
                          className="w-16"
                          type="number"
                          value={passYardsPoints}
                          onChange={(e) => setPassYardsPoints(Number(e.target.value))}
                        />
                        <span className="text-gray-500 text-sm">pt per</span>
                        <Input
                          className="w-16"
                          type="number"
                          value={passYardsPer}
                          onChange={(e) => setPassYardsPer(Number(e.target.value))}
                        />
                        <span className="text-gray-500 text-sm">yds</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 items-center gap-3">
                      <Label className="col-span-2">Interception</Label>
                      <Input
                        type="number"
                        value={interception}
                        onChange={(e) => setInterception(Number(e.target.value))}
                      />
                    </div>
                  </div>
                </div>
              )}

              {section === "Draft Details" && (
                <div className="space-y-6">
                  <div className="grid gap-2 max-w-sm">
                    <Label>Draft type</Label>
                    <Select value={draftType} onValueChange={setDraftType}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Snake">Snake</SelectItem>
                        <SelectItem value="Auction">Auction</SelectItem>
                        <SelectItem value="Linear">Linear</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid gap-2 max-w-md">
                    <Label>Number of Rounds</Label>
                    <Stepper value={rounds} onChange={setRounds} min={1} max={50} />
                  </div>

                  <div className="grid sm:grid-cols-[200px_160px] items-end gap-4 max-w-xl">
                    <div className="grid gap-2">
                      <Label>Draft Date</Label>
                      <Input type="date" value={draftDate} onChange={(e) => setDraftDate(e.target.value)} />
                    </div>
                    <div className="grid gap-2">
                      <Label>Time</Label>
                      <Input type="time" value={draftTime} onChange={(e) => setDraftTime(e.target.value)} />
                    </div>
                  </div>

                  <div className="grid gap-2 max-w-sm">
                    <Label>Your Default Rankings</Label>
                    <Select value={defaultRanks} onValueChange={setDefaultRanks}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select rankings" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Most Accurate Experts">Most Accurate Experts</SelectItem>
                        <SelectItem value="Consensus (All)">Consensus (All)</SelectItem>
                        <SelectItem value="User Custom">User Custom</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}

              {section === "Draft Order" && (
                <div className="space-y-6">
                  <h3 className="text-xl font-semibold">Reset Draft Order</h3>
                  <p className="text-gray-600 max-w-2xl">
                    Resetting your draft order will immediately remove any pick customizations you have made.
                  </p>
                  <Button className="bg-blue-600 hover:bg-blue-700 w-fit">Reset Draft Order</Button>
                </div>
              )}
            </div>
          </div>
          <Separator />
          <DialogFooter className="px-4 md:px-6 py-4">
            <DialogClose asChild>
              <Button variant="outline">Cancel</Button>
            </DialogClose>
            <Button className="bg-blue-600 hover:bg-blue-700" onClick={save}>
              Save Settings
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  )
}
