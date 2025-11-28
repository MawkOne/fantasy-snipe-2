"use client"

import { useMemo, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Lock, Wand2 } from "lucide-react"
import { NumberStepper } from "@/components/number-stepper"

type Scoring = "points" | "categories" | "custom"
type DraftType = "snake" | "linear" | "auction" | "custom"

export default function DraftSettings() {
  const [provider, setProvider] = useState("Yahoo")
  const [leagueType, setLeagueType] = useState<"season" | "dynasty">("season")
  const [scoring, setScoring] = useState<Scoring>("points")
  const [draftType, setDraftType] = useState<DraftType>("snake")
  const [opponentLogic, setOpponentLogic] = useState<"basic" | "advanced">("basic")
  const [teams, setTeams] = useState(12)
  const [draftPos, setDraftPos] = useState("11th")
  const [pickClock, setPickClock] = useState("None")

  const [roster, setRoster] = useState({
    C: 2,
    LW: 2,
    RW: 2,
    D: 4,
    G: 2,
    Util: 1,
    Bench: 5,
    IR: 1,
  })

  const draftPositions = useMemo(
    () => [
      "1st",
      "2nd",
      "3rd",
      "4th",
      "5th",
      "6th",
      "7th",
      "8th",
      "9th",
      "10th",
      "11th",
      "12th",
      "13th",
      "14th",
      "15th",
      "16th",
    ],
    [],
  )
  const pickClocks = ["None", "30s", "45s", "60s", "90s", "120s"]

  function startMock() {
    const q = new URLSearchParams({
      leagueType,
      scoring,
      draftType,
      teams: String(teams),
      draftPos,
      pickClock,
    }).toString()
    window.location.href = `/draft-room?${q}`
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Draft Configuration</h1>
        <p className="text-gray-600 text-sm">Customize your mock draft settings below</p>
      </div>

      {/* Sync league settings */}
      <Card>
        <CardContent className="p-4 md:p-6 space-y-4">
          <div className="text-sm font-medium">Sync Your League Settings From</div>
          <div className="flex flex-wrap items-center gap-3">
            <Select defaultValue={provider} onValueChange={setProvider}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Yahoo">Yahoo</SelectItem>
                <SelectItem value="ESPN">ESPN</SelectItem>
                <SelectItem value="CBS">CBS</SelectItem>
                <SelectItem value="Sleeper">Sleeper</SelectItem>
                <SelectItem value="Fantrax">Fantrax</SelectItem>
              </SelectContent>
            </Select>
            <Link href="/sync">
              <Button variant="outline" className="bg-transparent">
                Sync Your League
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Core settings */}
      <Card>
        <CardContent className="p-4 md:p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {/* League Type */}
            <fieldset>
              <legend className="text-sm font-medium mb-2">League Type</legend>
              <div className="flex items-center gap-4">
                <label className="inline-flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="league-type"
                    checked={leagueType === "season"}
                    onChange={() => setLeagueType("season")}
                  />
                  2025 Season
                </label>
                <label className="inline-flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="league-type"
                    checked={leagueType === "dynasty"}
                    onChange={() => setLeagueType("dynasty")}
                  />
                  Dynasty
                </label>
              </div>
            </fieldset>

            {/* Scoring */}
            <fieldset>
              <legend className="text-sm font-medium mb-2">Scoring</legend>
              <div className="flex items-center gap-4">
                <label className="inline-flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="scoring"
                    checked={scoring === "points"}
                    onChange={() => setScoring("points")}
                  />
                  Points
                </label>
                <label className="inline-flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="scoring"
                    checked={scoring === "categories"}
                    onChange={() => setScoring("categories")}
                  />
                  Categories
                </label>
                <label className="inline-flex items-center gap-2 text-sm opacity-60">
                  <input type="radio" name="scoring" disabled />
                  Custom <Lock className="w-3 h-3 text-orange-500" />
                </label>
              </div>
            </fieldset>

            {/* Draft Type */}
            <fieldset>
              <legend className="text-sm font-medium mb-2">Draft Type</legend>
              <div className="flex items-center gap-4">
                <label className="inline-flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="draft-type"
                    checked={draftType === "snake"}
                    onChange={() => setDraftType("snake")}
                  />
                  Snake
                </label>
                <label className="inline-flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="draft-type"
                    checked={draftType === "linear"}
                    onChange={() => setDraftType("linear")}
                  />
                  Linear
                </label>
                <label className="inline-flex items-center gap-2 text-sm opacity-60">
                  <input type="radio" name="draft-type" disabled />
                  Salary Cap <Lock className="w-3 h-3 text-orange-500" />
                </label>
                <label className="inline-flex items-center gap-2 text-sm opacity-60">
                  <input type="radio" name="draft-type" disabled />
                  Custom <Lock className="w-3 h-3 text-orange-500" />
                </label>
              </div>
            </fieldset>

            {/* Opponent Logic */}
            <fieldset>
              <legend className="text-sm font-medium mb-2">Opponent Pick Logic</legend>
              <div className="flex items-center gap-4">
                <label className="inline-flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="opp-logic"
                    checked={opponentLogic === "basic"}
                    onChange={() => setOpponentLogic("basic")}
                  />
                  Basic
                </label>
                <label className="inline-flex items-center gap-2 text-sm opacity-60">
                  <input type="radio" name="opp-logic" disabled />
                  Advanced <Lock className="w-3 h-3 text-orange-500" />
                </label>
              </div>
            </fieldset>

            {/* Teams */}
            <div>
              <Label className="text-sm font-medium mb-2 block"># of Teams</Label>
              <Select defaultValue={String(teams)} onValueChange={(v) => setTeams(Number(v))}>
                <SelectTrigger className="w-28">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Array.from({ length: 15 }, (_, i) => i + 6).map((n) => (
                    <SelectItem value={String(n)} key={n}>
                      {n}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Draft Position */}
            <div>
              <Label className="text-sm font-medium mb-2 block">Draft Position</Label>
              <div className="flex items-center gap-2">
                <Select defaultValue={draftPos} onValueChange={setDraftPos}>
                  <SelectTrigger className="w-28">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {draftPositions.map((p) => (
                      <SelectItem value={p} key={p}>
                        {p}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button variant="outline" className="bg-transparent" onClick={() => setDraftPos("Randomize")}>
                  Randomize
                </Button>
              </div>
            </div>

            {/* Pick Clock */}
            <div>
              <Label className="text-sm font-medium mb-2 block">Pick Clock</Label>
              <Select defaultValue={pickClock} onValueChange={setPickClock}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {pickClocks.map((t) => (
                    <SelectItem value={t} key={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Roster Positions */}
          <div className="pt-4">
            <div className="text-sm font-medium mb-3">Roster Positions</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(roster).map(([pos, val]) => (
                <div key={pos} className="flex items-center justify-between rounded-md border bg-white p-3">
                  <div className="text-sm">
                    <div className="font-medium">{pos}</div>
                    <div className="text-gray-500 text-xs">Slots</div>
                  </div>
                  <NumberStepper
                    value={val as number}
                    setValue={(n) => setRoster((r) => ({ ...r, [pos]: n }))}
                    min={pos === "IR" ? 0 : 0}
                    max={pos === "Bench" ? 10 : 6}
                  />
                </div>
              ))}
            </div>
            <button className="text-blue-600 text-sm mt-3 hover:underline" type="button">
              Show More Positions
            </button>
          </div>

          {/* Premium settings teaser */}
          <div className="rounded-md border p-4 bg-gray-50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="border-orange-400 text-orange-600">
                <Lock className="w-3 h-3 mr-1" />
                Premium
              </Badge>
              <div className="text-sm">
                <div className="font-medium">Premium Settings</div>
                <div className="text-gray-600">Enable advanced opponent logic, custom scoring weights, and more.</div>
              </div>
            </div>
            <Link href="/premium">
              <Button className="bg-blue-600 hover:bg-blue-700">Upgrade</Button>
            </Link>
          </div>

          <div className="flex items-center justify-end gap-3">
            <Link href="/draft-wizard/mock-draft-simulator">
              <Button variant="outline" className="bg-transparent">
                Back
              </Button>
            </Link>
            <Button onClick={startMock} className="bg-blue-600 hover:bg-blue-700">
              <Wand2 className="w-4 h-4 mr-2" />
              Start Mock Draft
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
