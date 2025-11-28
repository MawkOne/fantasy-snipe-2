import Link from "next/link"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Quote, PlayCircle, Users, BarChart3, Sparkles, ClipboardList, Trophy } from "lucide-react"

export default function DraftSimulatorLanding() {
  const features = [
    {
      icon: Sparkles,
      title: "Draft Simulator",
      desc: "Run instant mock drafts with AI opponents that adapt to your strategy.",
      href: "#draft-simulator",
    },
    {
      icon: Users,
      title: "Mock Draft Lobby",
      desc: "Practice live with friends or the community in private/public rooms.",
      href: "#mock-lobby",
    },
    {
      icon: BarChart3,
      title: "Draft Analyzer",
      desc: "Get post‑draft grades with deep category and roster balance insights.",
      href: "#draft-analyzer",
    },
    {
      icon: ClipboardList,
      title: "Draft Assistant",
      desc: "On‑the‑clock pick suggestions tailored to your league settings.",
      href: "#draft-assistant",
    },
  ]

  const steps = [
    {
      icon: Trophy,
      title: "Choose Format",
      desc: "Points or Categories. Centers, Wings, Defense, Goalies — fully configurable.",
    },
    {
      icon: Users,
      title: "Pick Opponents",
      desc: "Draft vs AI profiles (sharp, balanced, upside‑chaser) or invite friends.",
    },
    {
      icon: Sparkles,
      title: "Draft With AI",
      desc: "Realtime recommendations, reach/steal detection, and trend alerts.",
    },
  ]

  return (
    <main>
      {/* Hero */}
      <section className="container mx-auto px-4 pt-10 pb-8 text-center">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-slate-900">
          The Ultimate Cheat Code for Your Draft
        </h1>
        <p className="text-slate-600 mt-3 max-w-2xl mx-auto">
          Upgrade to FantasySnipe.ai’s Draft Wizard and get the smartest fantasy hockey draft tools on the planet.
        </p>

        <div className="flex items-center justify-center gap-3 mt-6">
          <Link href="/sync">
            <Button className="bg-blue-600 hover:bg-blue-700">Sync Your League</Button>
          </Link>
          <Link href="/draft-wizard/mock-draft-simulator/settings">
            <Button variant="outline" className="bg-transparent">
              Try a Mock Draft
            </Button>
          </Link>
        </div>

        {/* Product screenshot mock */}
        <div className="relative mx-auto mt-8 max-w-5xl rounded-xl border bg-white shadow-sm overflow-hidden">
          <div className="relative w-full h-[380px] md:h-[440px]">
            <Image
              src={
                "/placeholder.svg?height=440&width=1200&query=hockey%20draft%20simulator%20ui%20mock%20screenshot%20with%20player%20list%20and%20on%20the%20clock%20panel" ||
                "/placeholder.svg"
              }
              alt="FantasySnipe.ai Draft Simulator preview"
              fill
              className="object-cover"
              priority
            />
          </div>
          <button
            type="button"
            className="absolute inset-0 m-auto w-16 h-16 flex items-center justify-center rounded-full bg-white/90 hover:bg-white transition"
            aria-label="Play overview video"
          >
            <PlayCircle className="w-12 h-12 text-blue-600" />
          </button>
        </div>
      </section>

      {/* Testimonial band */}
      <section className="bg-amber-50 border-y">
        <div className="container mx-auto px-4 py-10 text-center">
          <Quote className="mx-auto w-8 h-8 text-amber-700 mb-4" />
          <p className="max-w-3xl mx-auto text-slate-700">
            I just want to say thanks for all the insights you put out there. I won my league following your
            recommendations.
          </p>
          <p className="text-slate-500 mt-2 text-sm">Mike, Team Schu — Tumbleweeds League</p>
        </div>
      </section>

      {/* Feature list */}
      <section className="container mx-auto px-4 py-10">
        <div className="grid md:grid-cols-2 gap-4">
          {features.map((f) => (
            <Card key={f.title} id={f.href.replace("#", "")} className="hover:shadow-md transition-shadow">
              <CardContent className="p-5 flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="mt-1 rounded-full bg-blue-100 p-2">
                    <f.icon className="w-5 h-5 text-blue-700" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">{f.title}</h3>
                    <p className="text-sm text-slate-600 mt-1">{f.desc}</p>
                  </div>
                </div>
                <Link href={f.href}>
                  <Button variant="outline" className="bg-transparent">
                    Learn More
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="bg-slate-50">
        <div className="container mx-auto px-4 py-12">
          <h2 className="text-2xl font-bold text-slate-900 text-center mb-6">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {steps.map((s, i) => (
              <Card key={s.title} className="text-center">
                <CardContent className="p-6">
                  <div className="mx-auto w-12 h-12 rounded-full bg-white border flex items-center justify-center mb-3">
                    <s.icon className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="text-xs text-slate-500 mb-1">Step {i + 1}</div>
                  <h3 className="font-semibold">{s.title}</h3>
                  <p className="text-sm text-slate-600 mt-2">{s.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="flex items-center justify-center gap-3 mt-8">
            <Link href="/draft-wizard/mock-draft-simulator/settings">
              <Button className="bg-blue-600 hover:bg-blue-700">Start Mock Draft</Button>
            </Link>
            <Link href="/sync">
              <Button variant="outline" className="bg-transparent">
                Import League Settings
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="container mx-auto px-4 py-12 text-center">
        <h3 className="text-xl font-semibold text-slate-900">Ready to draft like a pro?</h3>
        <p className="text-slate-600 mt-1">Run a mock in under 60 seconds with AI that adapts to your strategy.</p>
        <div className="mt-5 flex items-center justify-center gap-3">
          <Link href="/draft-wizard/mock-draft-simulator/settings">
            <Button className="bg-blue-600 hover:bg-blue-700">Try a Mock Draft</Button>
          </Link>
          <Link href="/sync">
            <Button variant="outline" className="bg-transparent">
              Sync Your League
            </Button>
          </Link>
        </div>
      </section>
    </main>
  )
}
