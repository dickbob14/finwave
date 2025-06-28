"use client"

import { useTemplates, useTemplateSnapshot } from "@/hooks/useTemplates"
import { KpiCardWithVariance } from "@/components/KpiCardWithVariance"
import { Button } from "@/components/ui/button"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { RefreshCw, Download } from "lucide-react"
import { useState } from "react"
import { apiPost } from "@/lib/api"
import { toast } from "sonner"

export default function TemplatesPage() {
  const { templates, isLoading: templatesLoading } = useTemplates()
  const [selectedTemplate, setSelectedTemplate] = useState("3statement")
  const { snapshot, isLoading: snapshotLoading, mutate } = useTemplateSnapshot(selectedTemplate)
  const [refreshing, setRefreshing] = useState(false)

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      // Get current date range (last 3 months)
      const endDate = new Date().toISOString().split('T')[0]
      const startDate = new Date()
      startDate.setMonth(startDate.getMonth() - 3)
      const startDateStr = startDate.toISOString().split('T')[0]
      
      const result = await apiPost(`/templates/${selectedTemplate}/populate?start_date=${startDateStr}&end_date=${endDate}`)
      
      if (result.download_url) {
        toast.success("Template populated with QuickBooks data!")
        // Automatically download the populated file
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${result.download_url}`)
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = result.populated_file
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
      mutate()
    } catch (error) {
      toast.error("Failed to populate template with data")
    } finally {
      setRefreshing(false)
    }
  }

  const handleDownload = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/templates/${selectedTemplate}/snapshot`)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `${selectedTemplate}-template.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success("Template downloaded")
    } catch (error) {
      toast.error("Failed to download template")
    }
  }

  if (templatesLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-secondary"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-primary">Financial Templates</h1>
          <p className="text-muted-foreground mt-2">Pre-built financial models and dashboards for your business</p>
        </div>
        <div className="flex space-x-4">
          <Button onClick={handleRefresh} disabled={refreshing} variant="outline">
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
            Populate with QuickBooks Data
          </Button>
          <Button onClick={handleDownload}>
            <Download className="w-4 h-4 mr-2" />
            Download Template
          </Button>
        </div>
      </div>

      {/* Template Selection */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {[
          { id: "3statement", name: "3-Statement Model", description: "Income Statement, Balance Sheet, Cash Flow" },
          { id: "budget", name: "Budget vs Actual", description: "Compare budgeted vs actual performance" },
          { id: "kpi", name: "KPI Dashboard", description: "Key performance indicators tracking" },
        ].map((template) => (
          <Card
            key={template.id}
            className={`cursor-pointer transition-all ${
              selectedTemplate === template.id ? "ring-2 ring-secondary" : ""
            }`}
            onClick={() => setSelectedTemplate(template.id)}
          >
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle className="text-lg">{template.name}</CardTitle>
                {selectedTemplate === template.id && <Badge className="bg-secondary">Active</Badge>}
              </div>
              <CardDescription>{template.description}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>

      {/* KPI Cards */}
      {snapshot && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KpiCardWithVariance
            title="Revenue"
            value="$2,450,000"
            trend="up"
            trendValue="+12.5% from last month"
            variance="none"
          />
          <KpiCardWithVariance
            title="Gross Margin"
            value="68.2%"
            trend="down"
            trendValue="-2.1% from last month"
            variance="warning"
          />
          <KpiCardWithVariance
            title="Operating Expenses"
            value="$890,000"
            trend="up"
            trendValue="+8.3% from last month"
            variance="critical"
          />
          <KpiCardWithVariance
            title="Net Income"
            value="$780,000"
            trend="up"
            trendValue="+15.2% from last month"
            variance="none"
          />
          <KpiCardWithVariance
            title="Cash Balance"
            value="$1,250,000"
            trend="up"
            trendValue="+5.8% from last month"
            variance="none"
          />
          <KpiCardWithVariance
            title="Accounts Receivable"
            value="$450,000"
            trend="neutral"
            trendValue="No change"
            variance="warning"
          />
          <KpiCardWithVariance
            title="Inventory"
            value="$320,000"
            trend="down"
            trendValue="-3.2% from last month"
            variance="none"
          />
          <KpiCardWithVariance
            title="Debt-to-Equity"
            value="0.35"
            trend="down"
            trendValue="-0.05 from last month"
            variance="none"
          />
        </div>
      )}
    </div>
  )
}
