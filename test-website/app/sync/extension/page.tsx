import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function SyncExtensionHelpPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <main className="container mx-auto px-4 py-8 max-w-3xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Sync via Chrome Extension</h1>
          <p className="text-gray-600 mt-2">Follow these steps to capture your CBS league data and sync it to FantasySnipe.</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Step 1 — Install the extension</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-gray-700">
              Install the FantasySnipe CBS Sync Chrome Extension. If you have a development build, open <b>chrome://extensions</b>, enable
              <b> Developer mode</b>, then choose <b>Load unpacked</b> and select the <code>chrome-extension</code> folder in this project.
            </p>
            <div className="flex gap-2">
              <Button asChild>
                <Link href="chrome://extensions/" target="_blank">Open chrome://extensions</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Step 2 — Log in to CBS</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-gray-700">Sign in to CBS Sports in a new tab.</p>
            <Button asChild variant="outline">
              <Link href="https://www.cbssports.com/login" target="_blank">Open CBS Login</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Step 3 — Go to your My Teams page</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-gray-700">Navigate to your fantasy My Teams page so the extension can read your leagues.</p>
            <Button asChild variant="outline">
              <Link href="https://www.cbssports.com/fantasy/games/my-teams/" target="_blank">Open CBS My Teams</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Step 4 — Open the extension and Sync</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-gray-700">
              Click the FantasySnipe extension icon, choose <b>Sync</b>, and wait for the confirmation. If there is a CAPTCHA or verification,
              complete it and retry. The extension will POST data to your account automatically.
            </p>
            <div className="flex gap-2">
              <Button asChild>
                <Link href="/sync">Return to Sync</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="text-sm text-gray-600">
          Having trouble? Make sure pop‑ups are allowed for CBS and try again. We recommend performing these steps in Chrome on desktop.
        </div>
      </main>
    </div>
  )
}


