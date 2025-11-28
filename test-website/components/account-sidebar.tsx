"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Settings, Mail, CreditCard, Gift, Trophy, LogOut } from "lucide-react"

const items = [
  { href: "/account/settings", label: "Account Settings", icon: Settings },
  { href: "/account/email-preferences", label: "Email Preferences", icon: Mail },
  { href: "/account/billing", label: "Billing", icon: CreditCard },
  { href: "/account/redeem", label: "Redeem", icon: Gift },
  // The main page we built
  { href: "/account", label: "My Leagues", icon: Trophy },
  { href: "/sign-out", label: "Sign Out", icon: LogOut },
]

export default function AccountSidebar() {
  const pathname = usePathname() || "/account"

  return (
    <nav className="p-4">
      <h2 className="text-lg font-semibold mb-3">My Account</h2>
      <ul className="space-y-1">
        {items.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/account" ? pathname === "/account" : pathname.startsWith(href) && href !== "/sign-out"
          return (
            <li key={href}>
              <Link
                href={href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition",
                  active ? "bg-blue-50 text-blue-700 border border-blue-100" : "text-gray-700 hover:bg-gray-50",
                )}
              >
                <Icon className="h-4 w-4" />
                <span className="flex-1">{label}</span>
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
