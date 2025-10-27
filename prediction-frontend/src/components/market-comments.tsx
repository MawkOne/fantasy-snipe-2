"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { MarketActivity } from "@/components/market-activity"
import { useState } from "react"

interface MarketCommentsProps {
  trades: any[]
  tradeCount: number
}

export function MarketComments({ trades, tradeCount }: MarketCommentsProps) {
  const [activeTab, setActiveTab] = useState("comments")
  const tabs = [
    { id: "comments", label: "Comments (24)" },
    { id: "holders", label: "Top Forecasters" },
    { id: "activity", label: `Activity (${tradeCount})` },
  ]

  const comments = [
    {
      id: 1,
      user: "HockeyAnalyst",
      avatar: "HA",
      time: "2h ago",
      position: "MORE $45 (avg)",
      text: "McDavid is on pace for 65 goals right now. The Oilers powerplay is clicking and he's getting prime opportunities every game. My forecast model has him at 62 goals.",
      likes: 12,
    },
    {
      id: 2,
      user: "StatNerd",
      avatar: "SN",
      time: "5h ago",
      position: "LESS $68 (avg)",
      text: "Historically, only 5 players have hit 60+ goals in the last 20 years. It's incredibly difficult to maintain that pace over 82 games. The consensus line seems too optimistic.",
      likes: 8,
    },
    {
      id: 3,
      user: "OilersSuperfan",
      avatar: "OS",
      time: "8h ago",
      position: "MORE $42 (avg)",
      text: "He's the best player in the world and he's motivated after last season. My playbook has him projected at 63 goals. I'm all in on MORE.",
      likes: 5,
    },
  ]

  return (
    <Card className="p-6">
      <div className="flex items-center gap-4 mb-6 border-b border-border">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`pb-3 px-1 text-sm font-medium transition-colors relative ${
              activeTab === tab.id ? "text-foreground" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
            {activeTab === tab.id && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />}
          </button>
        ))}
      </div>

      {activeTab === "comments" && (
        <>
          {/* Add Comment */}
          <div className="mb-6">
            <Textarea placeholder="Share your forecast analysis..." className="mb-2" />
            <div className="flex justify-end">
              <Button size="sm">Post</Button>
            </div>
          </div>

          {/* Comments List */}
          <div className="space-y-6">
            {comments.map((comment) => (
              <div key={comment.id} className="flex gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border border-border/50 flex-shrink-0">
                  <span className="text-sm font-bold text-primary">{comment.avatar}</span>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-sm">{comment.user}</span>
                    <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded">{comment.position}</span>
                    <span className="text-xs text-muted-foreground">{comment.time}</span>
                  </div>
                  <p className="text-sm text-foreground mb-2">{comment.text}</p>
                  <button className="text-xs text-muted-foreground hover:text-foreground">↑ {comment.likes}</button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {activeTab === "holders" && (
        <div className="text-sm text-muted-foreground">Top forecasters coming soon...</div>
      )}

      {activeTab === "activity" && <MarketActivity trades={trades} />}
    </Card>
  )
}
