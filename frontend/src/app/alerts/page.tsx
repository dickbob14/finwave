"use client"

import React, { useState } from 'react'
import useSWR from 'swr'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { 
  AlertCircle, 
  AlertTriangle, 
  Info,
  CheckCircle,
  TrendingUp,
  TrendingDown
} from 'lucide-react'
import { fetcher } from '@/lib/utils'
import { format } from 'date-fns'

interface Alert {
  id: string
  metric_id: string
  metric_name: string
  severity: 'critical' | 'warning' | 'info'
  message: string
  current_value: number
  threshold_value: number
  triggered_at: string
  acknowledged: boolean
}

export default function AlertsPage() {
  const workspaceId = 'demo'
  const [filter, setFilter] = useState<'all' | 'active' | 'acknowledged'>('active')
  
  const { data, error, mutate } = useSWR(
    `/api/${workspaceId}/alerts?status=${filter}`,
    fetcher
  )
  
  const acknowledgeAlert = async (alertId: string) => {
    try {
      await fetch(`/api/${workspaceId}/alerts/${alertId}/acknowledge`, {
        method: 'POST'
      })
      mutate()
    } catch (error) {
      console.error('Failed to acknowledge alert:', error)
    }
  }
  
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-amber-600" />
      default:
        return <Info className="h-4 w-4 text-blue-600" />
    }
  }
  
  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <Badge variant="destructive">Critical</Badge>
      case 'warning':
        return <Badge variant="warning">Warning</Badge>
      default:
        return <Badge variant="info">Info</Badge>
    }
  }
  
  const alerts = data?.alerts || []
  const activeAlerts = alerts.filter((a: Alert) => !a.acknowledged)
  
  return (
    <div className="container mx-auto p-6 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Variance Alerts</h1>
        <p className="text-muted-foreground mt-1">
          Monitor metrics that deviate from expected values
        </p>
      </div>
      
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium">Active Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeAlerts.length}</div>
            <p className="text-xs text-muted-foreground">
              Requiring attention
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium">Critical</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {activeAlerts.filter((a: Alert) => a.severity === 'critical').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Immediate action needed
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium">This Week</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {alerts.filter((a: Alert) => {
                const alertDate = new Date(a.triggered_at)
                const weekAgo = new Date()
                weekAgo.setDate(weekAgo.getDate() - 7)
                return alertDate > weekAgo
              }).length}
            </div>
            <p className="text-xs text-muted-foreground">
              New variance alerts
            </p>
          </CardContent>
        </Card>
      </div>
      
      {/* Filter Tabs */}
      <div className="flex gap-2">
        <Button
          variant={filter === 'active' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('active')}
        >
          Active
        </Button>
        <Button
          variant={filter === 'all' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('all')}
        >
          All
        </Button>
        <Button
          variant={filter === 'acknowledged' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('acknowledged')}
        >
          Acknowledged
        </Button>
      </div>
      
      {/* Alerts Table */}
      <Card>
        <CardHeader>
          <CardTitle>Alerts</CardTitle>
          <CardDescription>
            Click acknowledge when you've reviewed an alert
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="text-center py-8 text-muted-foreground">
              Failed to load alerts
            </div>
          ) : !data ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading alerts...
            </div>
          ) : alerts.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
              <p className="text-muted-foreground">No alerts to show</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Severity</TableHead>
                  <TableHead>Metric</TableHead>
                  <TableHead>Alert</TableHead>
                  <TableHead>Values</TableHead>
                  <TableHead>Time</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {alerts.map((alert: Alert) => (
                  <TableRow 
                    key={alert.id}
                    className={alert.acknowledged ? 'opacity-50' : ''}
                  >
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getSeverityIcon(alert.severity)}
                        {getSeverityBadge(alert.severity)}
                      </div>
                    </TableCell>
                    <TableCell className="font-medium">
                      {alert.metric_name}
                    </TableCell>
                    <TableCell>{alert.message}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          {typeof alert.current_value === 'number' 
                            ? alert.current_value.toLocaleString() 
                            : alert.current_value}
                        </span>
                        {alert.current_value > alert.threshold_value ? (
                          <TrendingUp className="h-4 w-4 text-red-600" />
                        ) : (
                          <TrendingDown className="h-4 w-4 text-green-600" />
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {format(new Date(alert.triggered_at), 'MMM d, h:mm a')}
                    </TableCell>
                    <TableCell>
                      {alert.acknowledged ? (
                        <Badge variant="outline">Acknowledged</Badge>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => acknowledgeAlert(alert.id)}
                        >
                          Acknowledge
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}