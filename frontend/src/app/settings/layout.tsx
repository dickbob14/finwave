"use client"

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  Settings, 
  Palette, 
  Users, 
  CreditCard, 
  Shield,
  Database,
  Bell
} from 'lucide-react'
import { cn } from '@/lib/utils'

const settingsNavItems = [
  {
    title: 'Branding',
    href: '/settings/branding',
    icon: Palette,
    description: 'Customize your company branding'
  },
  {
    title: 'Team',
    href: '/settings/team',
    icon: Users,
    description: 'Manage team members and permissions'
  },
  {
    title: 'Billing',
    href: '/settings/billing',
    icon: CreditCard,
    description: 'Manage subscription and payment'
  },
  {
    title: 'Integrations',
    href: '/settings/integrations',
    icon: Database,
    description: 'Connect data sources'
  },
  {
    title: 'Notifications',
    href: '/settings/notifications',
    icon: Bell,
    description: 'Configure alerts and notifications'
  },
  {
    title: 'Security',
    href: '/settings/security',
    icon: Shield,
    description: 'Security and privacy settings'
  }
]

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <div className="w-64 bg-gray-50 border-r">
        <div className="p-6">
          <div className="flex items-center gap-2 mb-8">
            <Settings className="w-6 h-6" />
            <h2 className="text-xl font-semibold">Settings</h2>
          </div>
          
          <nav className="space-y-1">
            {settingsNavItems.map((item) => {
              const isActive = pathname === item.href
              const Icon = item.icon
              
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
                    isActive 
                      ? "bg-blue-600 text-white" 
                      : "hover:bg-gray-100 text-gray-700"
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <div>
                    <div className="font-medium">{item.title}</div>
                    {isActive && (
                      <div className="text-xs opacity-80 mt-0.5">
                        {item.description}
                      </div>
                    )}
                  </div>
                </Link>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 bg-white">
        {children}
      </div>
    </div>
  )
}