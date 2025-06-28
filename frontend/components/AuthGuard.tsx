"use client"

import type React from "react"

interface AuthGuardProps {
  children: React.ReactNode
}

export const AuthGuard = ({ children }: AuthGuardProps) => {
  // Remove authentication requirement for demo purposes
  return <>{children}</>
}
