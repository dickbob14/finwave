"use client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { AlertTriangle, CheckCircle, AlertCircle, Clock } from "lucide-react"
import { useState } from "react"

const mockAlerts = [
  {
    id: "1",
    title: "Revenue Variance Alert",
    description: "Q4 revenue is 15% below forecast",
    severity: "critical",
    status: "active",
    created_at: "2024-01-15T10:30:00Z",
    metric: "Revenue",
    variance: -15.2,
  },
  {
    id: "2",
    title: "Cash Flow Warning",
    description: "Operating cash flow trending below target",
    severity: "warning",
    status: "active",
    created_at: "2024-01-14T14:20:00Z",
    metric: "Operating Cash Flow",
    variance: -8.5,
  },
  {
    id: "3",
    title: "Expense Spike Detected",
    description: "Marketing expenses exceeded budget by 20%",
    severity: "warning",
    status: "acknowledged",
    created_at: "2024-01-13T09:15:00Z",
    metric: "Marketing Expenses",
    variance: 20.3,
  },
]

export default function AlertsPage() {
  const [filter, setFilter] = useState<"all" | "active" | "acknowledged">("active")
  const [alerts, setAlerts] = useState(mockAlerts)

  const handleAcknowledge = (alertId: string) => {
    setAlerts((prev) => prev.map((alert) => (alert.id === alertId ? { ...alert, status: "acknowledged" } : alert)))
  }

  const getAlertIcon = (severity: string) => {
    switch (severity) {
      case "critical":
        return <AlertCircle className="h-5 w-5 text-error" />
      case "warning":
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      default:
        return <CheckCircle className="h-5 w-5 text-success" />
    }
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "critical":
        return <Badge className="bg-error text-white">Critical</Badge>
      case "warning":
        return <Badge className="bg-yellow-500 text-white">Warning</Badge>
      default:
        return <Badge className="bg-success text-white">Info</Badge>
    }
  }

  const filteredAlerts = alerts.filter((alert) => {
    if (filter === "all") return true
    return alert.status === filter
  })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-primary">Variance Alerts</h1>
          <p className="text-muted-foreground mt-2">Monitor and manage financial variance alerts</p>
        </div>
        <div className="flex space-x-2">
          {(["all", "active", "acknowledged"] as const).map((status) => (
            <Button
              key={status}
              variant={filter === status ? "default" : "outline"}
              onClick={() => setFilter(status)}
              className="capitalize"
            >
              {status}
            </Button>
          ))}
        </div>
      </div>

      {/* Alert Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <AlertCircle className="h-4 w-4 text-error" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{alerts.filter((a) => a.status === "active").length}</div>
            <p className="text-xs text-muted-foreground">Require attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{alerts.filter((a) => a.severity === "critical").length}</div>
            <p className="text-xs text-muted-foreground">High priority</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resolved Today</CardTitle>
            <CheckCircle className="h-4 w-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">Acknowledged alerts</p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {filteredAlerts.map((alert) => (
          <Card key={alert.id} className="relative">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  {getAlertIcon(alert.severity)}
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <CardTitle className="text-lg">{alert.title}</CardTitle>
                      {getSeverityBadge(alert.severity)}
                      {alert.status === "acknowledged" && <Badge variant="outline">Acknowledged</Badge>}
                    </div>
                    <CardDescription className="text-base">{alert.description}</CardDescription>
                  </div>
                </div>
                {alert.status === "active" && (
                  <Button onClick={() => handleAcknowledge(alert.id)} variant="outline" size="sm">
                    Acknowledge
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <div className="flex items-center space-x-4">
                  <span className="flex items-center">
                    <Clock className="h-4 w-4 mr-1" />
                    {new Date(alert.created_at).toLocaleDateString()}
                  </span>
                  <span>Metric: {alert.metric}</span>
                  <span className={`font-semibold ${alert.variance > 0 ? "text-error" : "text-success"}`}>
                    {alert.variance > 0 ? "+" : ""}
                    {alert.variance}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredAlerts.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <CheckCircle className="h-12 w-12 text-success mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No alerts found</h3>
            <p className="text-muted-foreground">
              {filter === "active"
                ? "All alerts have been acknowledged or resolved."
                : `No ${filter} alerts at this time.`}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
