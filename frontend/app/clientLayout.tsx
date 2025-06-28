"use client"

import type React from "react"
import "./globals.css"
import { Navigation } from "@/components/Navigation"
import { Toaster } from "sonner"
import { usePathname } from "next/navigation"

function LayoutContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isLoginPage = pathname === "/login"

  if (isLoginPage) {
    return children
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main>{children}</main>
    </div>
  )
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        <LayoutContent>{children}</LayoutContent>
        <Toaster position="top-right" />
      </body>
    </html>
  )
}
