"use client"

import { useInsights, askAI } from "@/lib/finwave"
import Chart from "@/components/Chart"
import KpiCard from "@/components/KpiCard" 
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { Brain, TrendingUp } from "lucide-react"

export default function DashboardPage() {
  const { insights, isLoading: insightsLoading, isError } = useInsights()
  const [aiResponse, setAiResponse] = useState<string | null>(null)
  const [aiLoading, setAiLoading] = useState(false)

  // Debug logging
  console.log("Dashboard State:", { insights, insightsLoading, isError })

  const handleAIAnalysis = async () => {
    setAiLoading(true)
    try {
      const response = await askAI("Tell me the key trends in my financial data")
      setAiResponse(response.ai_analysis)
    } catch (error) {
      console.error("AI Analysis error:", error)
      setAiResponse("Failed to get AI analysis. Check console for details.")
    } finally {
      setAiLoading(false)
    }
  }

  if (insightsLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center h-64">
          <Card className="bg-red-50 border-red-200">
            <CardContent className="p-6">
              <h3 className="text-red-800 font-medium mb-2">QuickBooks Connection Error</h3>
              <p className="text-red-600 text-sm mb-4">
                Unable to fetch data from QuickBooks. This could be because:
              </p>
              <ul className="text-red-600 text-sm list-disc list-inside space-y-1">
                <li>QuickBooks is not connected</li>
                <li>API connection failed</li>
                <li>Authentication expired</li>
              </ul>
              <Button 
                className="mt-4" 
                onClick={() => window.open('http://localhost:8000/connect_qb', '_blank')}
              >
                Connect QuickBooks
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            AI-powered financial insights and analytics
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="h-2 w-2 bg-green-500 rounded-full"></div>
          <span className="text-sm text-gray-600 dark:text-gray-300">
            Live Data
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KpiCard
          title="Total Revenue"
          value={insights?.key_metrics.total_revenue || "$0.00"}
          change="Live QuickBooks data"
          trend="up"
          description="Current period revenue"
        />
        <KpiCard
          title="Net Profit"
          value={insights?.key_metrics.net_profit || "$0.00"}
          change={insights?.key_metrics.profit_margin || "0%"}
          trend="up"
          description="Profit margin"
        />
        <KpiCard
          title="Total Expenses"
          value={insights?.key_metrics.total_expenses || "$0.00"}
          change="Expense tracking"
          trend="neutral"
          description="Period expenses"
        />
        <KpiCard
          title="Accounts Receivable"
          value={insights?.key_metrics.accounts_receivable || "$0.00"}
          change={`${insights?.key_metrics.outstanding_invoices || 0} invoices`}
          trend="down"
          description="Outstanding receivables"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Chart
          type="revenue-trend"
          title="Revenue Trend"
          description="Monthly revenue growth over the last 6 months"
        />
        
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Brain className="h-5 w-5 mr-2" />
              AI Financial Analysis
            </CardTitle>
            <CardDescription>
              Get AI-powered insights about your financial trends
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button 
              onClick={handleAIAnalysis}
              disabled={aiLoading}
              className="w-full"
            >
              {aiLoading ? "Analyzing..." : "Get AI Insights"}
            </Button>
            
            {aiResponse && (
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {aiResponse}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Insights and Recommendations */}
      {insights && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <TrendingUp className="h-5 w-5 mr-2" />
                AI Recommendations
              </CardTitle>
              <CardDescription>
                Actionable insights to improve your business
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {insights.ai_recommendations.map((recommendation, index) => (
                  <li key={index} className="flex items-start">
                    <div className="h-2 w-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      {recommendation}
                    </p>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <span className="h-2 w-2 bg-yellow-500 rounded-full mr-2"></span>
                Variance Alerts
              </CardTitle>
              <CardDescription>
                Items that need your attention
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {insights.variance_alerts.map((alert, index) => (
                  <li key={index} className="flex items-start">
                    <div className="h-2 w-2 bg-yellow-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      {alert}
                    </p>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}