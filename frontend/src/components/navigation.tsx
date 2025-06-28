'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { 
  BarChart3, 
  FileSpreadsheet, 
  MessageSquare,
  Home,
  Settings,
  TrendingUp,
  Bell,
  LayoutDashboard
} from 'lucide-react'
import Image from 'next/image'

const navItems = [
  {
    title: 'Dashboard',
    href: '/',
    icon: LayoutDashboard
  },
  {
    title: 'Templates',
    href: '/templates',
    icon: FileSpreadsheet
  },
  {
    title: 'Scenarios',
    href: '/scenario-planning',
    icon: TrendingUp
  },
  {
    title: 'Alerts',
    href: '/alerts',
    icon: Bell
  },
  {
    title: 'Ask AI',
    href: '/ask',
    icon: MessageSquare
  },
  {
    title: 'API Explorer',
    href: '/explorer',
    icon: BarChart3
  }
]

export function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="border-b border-gray-200 bg-white shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="relative h-10 w-10 bg-gradient-to-r from-secondary to-accent rounded-lg flex items-center justify-center group-hover:scale-105 transition-transform">
                <div className="absolute inset-0 bg-gradient-to-r from-secondary to-accent rounded-lg opacity-20 blur-lg group-hover:opacity-30 transition-opacity"></div>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="relative z-10">
                  <path d="M3 9C4.5 6 7 6 9 9C11 12 13 12 15 9C17 6 19.5 6 21 9" stroke="white" strokeWidth="2" strokeLinecap="round"/>
                  <path d="M3 15C4.5 12 7 12 9 15C11 18 13 18 15 15C17 12 19.5 12 21 15" stroke="white" strokeWidth="2" strokeLinecap="round" opacity="0.8"/>
                </svg>
              </div>
              <span className="text-xl font-display font-semibold text-primary">FinWave</span>
            </Link>
            
            <div className="hidden md:flex items-center gap-6">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href || 
                  (item.href !== '/' && pathname.startsWith(item.href))
                
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2 text-sm font-medium transition-all duration-200",
                      isActive 
                        ? "text-secondary" 
                        : "text-primary/70 hover:text-secondary"
                    )}
                  >
                    <Icon className={cn(
                      "h-4 w-4 transition-colors",
                      isActive && "text-secondary"
                    )} />
                    {item.title}
                  </Link>
                )
              })}
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <Link 
              href="/settings/branding" 
              className="text-primary/70 hover:text-secondary transition-colors"
              title="Settings"
            >
              <Settings className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}
