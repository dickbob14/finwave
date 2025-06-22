"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function TestPage() {
  const [healthData, setHealthData] = useState<any>(null)
  const [insightsData, setInsightsData] = useState<any>(null)
  const [transactionsData, setTransactionsData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const testHealth = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch("http://localhost:8000/health")
      const data = await response.json()
      setHealthData(data)
    } catch (err) {
      setError("Health check failed: " + err)
    } finally {
      setLoading(false)
    }
  }

  const testInsights = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch("http://localhost:8000/real/insights")
      const data = await response.json()
      setInsightsData(data)
    } catch (err) {
      setError("Insights fetch failed: " + err)
    } finally {
      setLoading(false)
    }
  }

  const testTransactions = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch("http://localhost:8000/real/transactions")
      const data = await response.json()
      setTransactionsData(data)
    } catch (err) {
      setError("Transactions fetch failed: " + err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">API Test Page</h1>
      
      <div className="space-x-4">
        <Button onClick={testHealth} disabled={loading}>
          Test Health
        </Button>
        <Button onClick={testInsights} disabled={loading}>
          Test Real Insights
        </Button>
        <Button onClick={testTransactions} disabled={loading}>
          Test Transactions
        </Button>
      </div>

      {error && (
        <Card className="bg-red-50 border-red-200">
          <CardHeader>
            <CardTitle className="text-red-800">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm">{error}</pre>
          </CardContent>
        </Card>
      )}

      {healthData && (
        <Card>
          <CardHeader>
            <CardTitle>Health Response</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm overflow-auto">
              {JSON.stringify(healthData, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {insightsData && (
        <Card>
          <CardHeader>
            <CardTitle>Insights Response</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm overflow-auto">
              {JSON.stringify(insightsData, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {transactionsData && (
        <Card>
          <CardHeader>
            <CardTitle>Transactions Response</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm overflow-auto">
              {JSON.stringify(transactionsData, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}