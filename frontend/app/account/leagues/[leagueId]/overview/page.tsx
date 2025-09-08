"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import SettingsDialog from "@/components/settings-dialog"

export default function LeagueOverviewPage() {
  const [open, setOpen] = useState(false)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr,340px] gap-6">
      {/* Left: Settings summary */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-xl">Settings</CardTitle>
          </div>
          <Button variant="link" className="text-blue-700" onClick={() => setOpen(true)}>
            Edit
          </Button>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <Section title="League">
                <Row label="League type" value="Keeper" />
                <Row label="Playoffs" value="6" />
                <Row label="Roster" value={"C, 2 LW, 2 RW, 4 D, 2 G, 5 BN"} />
              </Section>
              <Section title="Draft">
                <Row label="Draft type" value="Snake" />
                <Row label="Draft position" value="10" />
              </Section>
            </div>

            <div className="space-y-4">
              <Section title=" ">
                <Row label="Teams" value="12 teams" />
                <Row label="Scoring" value="Custom" />
              </Section>
              <Section title=" ">
                <Row label="No. rounds" value="15" />
                <Row label="Draft date" value="Thu Aug 28 2025" />
              </Section>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Right: Action cards */}
      <div className="space-y-4">
        <ActionCard
          title="Draft Simulator"
          desc="Practice for your draft by mock drafting with your league settings."
          button={{ label: "Mock Draft", href: "/draft-wizard/mock-draft-simulator" }}
        />
        <ActionCard
          title="Draft Assistant w/ Live Sync"
          desc="Connect to your live draft to get the best possible expert advice at every pick."
          meta={
            <p className="text-xs text-gray-600">
              You currently have 0 picks saved (
              <a className="underline" href="#">
                delete
              </a>
              )
            </p>
          }
          button={{ label: "Live Draft Assistant", href: "/draft-room" }}
        />
        <ActionCard
          title="Manual Draft Assistant"
          desc="If your draft is offline, or live assistant is unavailable, track picks yourself and get the same expert suggestions and advice."
          button={{ label: "Manual Draft Assistant", href: "/draft-wizard/mock-draft-simulator" }}
        />
      </div>

      <SettingsDialog open={open} onOpenChange={setOpen} />
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-gray-200 p-4">
      {title.trim() && <h3 className="font-semibold mb-3">{title}</h3>}
      <div className="space-y-3">{children}</div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string | React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="text-gray-600">{label}</div>
      <div className="font-medium text-right">{value}</div>
    </div>
  )
}

function ActionCard({
  title,
  desc,
  meta,
  button,
}: {
  title: string
  desc: string
  meta?: React.ReactNode
  button: { label: string; href: string }
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-gray-700">{desc}</p>
        {meta}
        <a href={button.href}>
          <Button className="w-full bg-blue-600 hover:bg-blue-700">{button.label}</Button>
        </a>
      </CardContent>
    </Card>
  )
}
