"use client"

import { useState, useEffect } from "react"

export const useAuth = () => {
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const storedToken = localStorage.getItem("token")
    setToken(storedToken)
    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    // Simulate login - just store a demo token
    localStorage.setItem("token", "demo-token-123")
    setToken("demo-token-123")
    return { token: "demo-token-123" }
  }

  const logout = () => {
    localStorage.removeItem("token")
    setToken(null)
  }

  return {
    token,
    isAuthenticated: !!token,
    isLoading,
    login,
    logout,
  }
}
