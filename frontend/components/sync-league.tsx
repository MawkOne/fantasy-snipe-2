"use client"

import { useMemo, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { ShieldCheck, LinkIcon, CheckCircle2, Loader2 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

type ProviderId = "yahoo" | "espn" | "cbs" | "sleeper" | "fantrax"

type League = {
  id: string
  name: string
  platform: string
  scoring: string
  teams: number
}

export default function SyncLeague() {
  const { toast } = useToast()
  const [selectedProvider, setSelectedProvider] = useState<ProviderId | null>(null)
  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [leagues, setLeagues] = useState<League[]>([])
  const [selectedLeagues, setSelectedLeagues] = useState<Record<string, boolean>>({})
  const [form, setForm] = useState({ username: "", password: "" })

  const providers = useMemo(
    () => [
      {
        id: "yahoo" as const,
        name: "Yahoo",
        desc: "Secure OAuth connection to your Yahoo Fantasy leagues.",
        accent: "bg-violet-600",
      },
      {
        id: "espn" as const,
        name: "ESPN",
        desc: "Connect with your ESPN Fantasy leagues.",
        accent: "bg-red-600",
      },
      {
        id: "cbs" as const,
        name: "CBS",
        desc: "Sync CBS Sports fantasy leagues.",
        accent: "bg-sky-700",
      },
      {
        id: "sleeper" as const,
        name: "Sleeper",
        desc: "Sync Sleeper leagues in seconds.",
        accent: "bg-emerald-600",
      },
      {
        id: "fantrax" as const,
        name: "Fantrax",
        desc: "Bring in your Fantrax configuration.",
        accent: "bg-blue-700",
      },
    ],
    [],
  )

  const sampleLeagues: League[] = [
    { id: "1", name: "Dynasty Cup 2025", platform: "Yahoo", scoring: "Points", teams: 12 },
    { id: "2", name: "Friends & Family", platform: "ESPN", scoring: "Categories", teams: 10 },
    { id: "3", name: "Work League", platform: "CBS", scoring: "Points", teams: 12 },
    { id: "4", name: "Sleeper Saturday", platform: "Sleeper", scoring: "Points", teams: 14 },
  ]

  function simulateConnect() {
    setIsConnecting(true)
    setTimeout(() => {
      setIsConnecting(false)
      setIsConnected(true)
      setLeagues(sampleLeagues)
      setSelectedLeagues({ 1: true, 3: true })
      toast({
        title: "Connected",
        description: "We discovered 4 leagues linked to your account.",
      })
    }, 1200)
  }

  function importSelected() {
    const count = Object.values(selectedLeagues).filter(Boolean).length
    if (count === 0) {
      toast({ title: "Select at least one league", description: "Choose leagues to import.", variant: "destructive" })
      return
    }
    toast({
      title: "Sync complete",
      description: `Imported ${count} league${count > 1 ? "s" : ""}. You can manage them in My Playbook.`,
    })
    // Reset
    setIsConnected(false)
    setLeagues([])
    setSelectedLeagues({})
    setSelectedProvider(null)
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div className="lg:col-span-2 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Sync Your League</h1>
          <p className="text-gray-600 mt-1">Connect your fantasy platform for personalized, in-season advice.</p>
        </div>

        {/* Providers grid only (CSV and linked/manual removed) */}
        <div className="grid sm:grid-cols-2 gap-4">
          {providers.map((p) => (
            <AuthCard
              key={p.id}
              title={p.name}
              description={p.desc}
              accentClass={p.accent}
              onConnect={() => setSelectedProvider(p.id)}
            />
          ))}
        </div>

        <Alert>
          <ShieldCheck className="h-4 w-4" />
          <AlertTitle>Secure. Read-only. Private.</AlertTitle>
          <AlertDescription>
            We use read-only access to fetch league settings and rosters. Your credentials are encrypted in transit and
            are never stored in plain text.
          </AlertDescription>
        </Alert>
      </div>

      {/* Right column: Connection + discovered leagues */}
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <LinkIcon className="w-5 h-5" />
              Connection
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!selectedProvider && (
              <p className="text-gray-600">Choose a provider on the left to begin syncing your league.</p>
            )}

            {/* Connect dialog */}
            {selectedProvider && !isConnected && (
              <ConnectDialog
                provider={selectedProvider}
                form={form}
                setForm={setForm}
                isConnecting={isConnecting}
                onCancel={() => setSelectedProvider(null)}
                onConnect={simulateConnect}
              />
            )}

            {/* Connected state */}
            {isConnected && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-green-700">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="font-medium">Connected. Select leagues to import.</span>
                </div>

                <div className="space-y-3">
                  {leagues.map((lg) => (
                    <div key={lg.id} className="flex items-center justify-between rounded-lg border p-3">
                      <div className="flex items-center gap-3">
                        <Checkbox
                          checked={!!selectedLeagues[lg.id]}
                          onCheckedChange={(v) => setSelectedLeagues((s) => ({ ...s, [lg.id]: Boolean(v) }))}
                        />
                        <div>
                          <div className="font-medium">{lg.name}</div>
                          <div className="text-xs text-gray-500">
                            {lg.platform} • {lg.scoring} • {lg.teams} teams
                          </div>
                        </div>
                      </div>
                      <Badge variant="outline">{lg.platform}</Badge>
                    </div>
                  ))}
                </div>

                <Button className="w-full" onClick={importSelected}>
                  Import Selected
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Support card (CSV removed) */}
        <Card>
          <CardHeader>
            <CardTitle>Need help connecting?</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-gray-600 text-sm">
              Having trouble with a provider? Make sure pop-up blockers are disabled and try again. You can also view
              our setup guide or contact support.
            </p>
            <div className="flex gap-2">
              <Button variant="outline" className="bg-transparent">
                View Setup Guide
              </Button>
              <Button variant="outline" className="bg-transparent">
                Contact Support
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function AuthCard({
  title,
  description,
  accentClass,
  onConnect,
}: {
  title: string
  description: string
  accentClass: string
  onConnect: () => void
}) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className={`h-1.5 w-12 rounded-full ${accentClass}`} />
        <CardTitle className="mt-2">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-gray-600">{description}</p>
        <Button onClick={onConnect} className="w-full">
          Connect
        </Button>
      </CardContent>
    </Card>
  )
}

function ConnectDialog({
  provider,
  form,
  setForm,
  isConnecting,
  onCancel,
  onConnect,
}: {
  provider: ProviderId
  form: { username: string; password: string }
  setForm: (f: { username: string; password: string }) => void
  isConnecting: boolean
  onCancel: () => void
  onConnect: () => void
}) {
  const providerName = provider === "cbs" ? "CBS" : provider.charAt(0).toUpperCase() + provider.slice(1)

  return (
    <Dialog open onOpenChange={(open) => (!open ? onCancel() : undefined)}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Connect {providerName}</DialogTitle>
          <DialogDescription>Enter your credentials to securely discover your leagues.</DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div>
            <Label htmlFor="username">Email or Username</Label>
            <Input
              id="username"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              placeholder="you@example.com"
            />
          </div>
          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder="••••••••"
            />
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" className="bg-transparent" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={onConnect} disabled={isConnecting}>
            {isConnecting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
            Connect
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
