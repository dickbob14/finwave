"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Sparkles } from "lucide-react"

const navItems = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/ask", label: "Ask FinWave", icon: Sparkles, highlight: true },
  { href: "/templates", label: "Templates" },
  { href: "/scenario-planning", label: "Scenario Planning" },
  { href: "/alerts", label: "Alerts" },
  { href: "/reports/history", label: "Reports" },
  { href: "/settings", label: "Settings" },
]

export const Navigation = () => {
  const pathname = usePathname()

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-3">
              <img
                src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Screenshot%202025-06-22%20at%204.27.55%E2%80%AFAM-dY8s0sTShZgyJNYE8FRwVx6FNoDXqd.png"
                alt="FinWave Logo"
                className="h-8 w-auto"
              />
            </Link>
          </div>

          <div className="flex items-center space-x-8">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2",
                    pathname === item.href
                      ? "text-secondary bg-secondary/10"
                      : item.highlight
                        ? "text-accent bg-accent/10 hover:bg-accent/20"
                        : "text-gray-600 hover:text-secondary hover:bg-secondary/5",
                  )}
                >
                  {Icon && <Icon className="h-4 w-4" />}
                  {item.label}
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}
