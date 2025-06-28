"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import { cn } from "@/lib/utils"

interface KPI {
  metric: string
  value: string
  change: string
  trend: "up" | "down" | "neutral"
  period?: string
}

interface KPITableProps {
  kpis: KPI[]
  title?: string
}

export function KPITable({ kpis, title = "Key Metrics" }: KPITableProps) {
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "up":
        return TrendingUp
      case "down":
        return TrendingDown
      default:
        return Minus
    }
  }

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case "up":
        return "text-success"
      case "down":
        return "text-error"
      default:
        return "text-muted-foreground"
    }
  }

  return (
    <Card className="border-accent/20 bg-accent/5">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <div className="w-2 h-2 bg-accent rounded-full"></div>
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {kpis.map((kpi, index) => {
            const TrendIcon = getTrendIcon(kpi.trend)
            return (
              <div key={index} className="flex items-center justify-between p-3 bg-background rounded-lg">
                <div className="flex-1">
                  <div className="font-medium text-sm">{kpi.metric}</div>
                  {kpi.period && <div className="text-xs text-muted-foreground">{kpi.period}</div>}
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold text-sm">{kpi.value}</div>
                  <div className={cn("flex items-center gap-1 text-xs", getTrendColor(kpi.trend))}>
                    <TrendIcon className="h-3 w-3" />
                    {kpi.change}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
