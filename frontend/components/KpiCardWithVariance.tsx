"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { VarianceBadge } from "./VarianceBadge"
import { TrendingUp, TrendingDown } from "lucide-react"
import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"

interface KpiCardProps {
  title: string
  value: string | number
  trend: "up" | "down" | "neutral"
  trendValue?: string
  variance: "none" | "warning" | "critical"
  metricId?: string
}

export const KpiCardWithVariance = ({ title, value, trend, trendValue, variance, metricId }: KpiCardProps) => {
  const [showInsight, setShowInsight] = useState(false)

  const handleVarianceClick = () => {
    if (variance !== "none") {
      setShowInsight(true)
    }
  }

  const formatValue = (val: string | number) => {
    if (typeof val === "number") {
      return val.toLocaleString()
    }
    return val
  }

  return (
    <>
      <Card className="relative">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
          <VarianceBadge variance={variance} onClick={handleVarianceClick} />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold font-mono">{formatValue(value)}</div>
          {trendValue && (
            <div className="flex items-center text-xs text-muted-foreground mt-1">
              {trend === "up" ? (
                <TrendingUp className="w-3 h-3 mr-1 text-success" />
              ) : trend === "down" ? (
                <TrendingDown className="w-3 h-3 mr-1 text-error" />
              ) : null}
              <span>{trendValue}</span>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={showInsight} onOpenChange={setShowInsight}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Variance Insight: {title}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-semibold mb-2">Alert Details</h4>
              <p className="text-sm text-muted-foreground">
                This metric is showing a {variance} variance from expected values.
                {variance === "critical" && " Immediate attention may be required."}
              </p>
            </div>
            <div className="p-4 bg-accent/10 rounded-lg">
              <h4 className="font-semibold mb-2">AI Insight</h4>
              <p className="text-sm">
                Based on historical patterns, this variance could be attributed to seasonal trends or recent market
                conditions. Consider reviewing the underlying data sources and recent business activities that might
                impact this metric.
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
