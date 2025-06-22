'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { 
  BarChart3, 
  FileSpreadsheet, 
  MessageSquare,
  Home,
  Settings
} from 'lucide-react'

const navItems = [
  {
    title: 'Home',
    href: '/',
    icon: Home
  },
  {
    title: 'Ask AI',
    href: '/ask',
    icon: MessageSquare
  },
  {
    title: 'Templates',
    href: '/templates',
    icon: FileSpreadsheet
  },
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: BarChart3
  }
]

export function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="border-b bg-white">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2">
              <BarChart3 className="h-6 w-6 text-blue-600" />
              <span className="text-xl font-bold">FinWave</span>
            </Link>
            
            <div className="hidden md:flex items-center gap-6">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2 text-sm font-medium transition-colors hover:text-blue-600",
                      isActive ? "text-blue-600" : "text-gray-600"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.title}
                  </Link>
                )
              })}
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <Link 
              href="/settings/branding" 
              className="text-gray-600 hover:text-gray-900"
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