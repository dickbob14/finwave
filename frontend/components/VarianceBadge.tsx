"use client"

import { Badge } from "@/components/ui/badge"
import { AlertTriangle, CheckCircle, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface VarianceBadgeProps {
  variance: "none" | "warning" | "critical"
  onClick?: () => void
}

export const VarianceBadge = ({ variance, onClick }: VarianceBadgeProps) => {
  const getVarianceConfig = () => {
    switch (variance) {
      case "none":
        return {
          icon: CheckCircle,
          className: "bg-success text-white",
          label: "On Track",
        }
      case "warning":
        return {
          icon: AlertTriangle,
          className: "bg-yellow-500 text-white",
          label: "Warning",
        }
      case "critical":
        return {
          icon: AlertCircle,
          className: "bg-error text-white animate-pulse",
          label: "Critical",
        }
      default:
        return {
          icon: CheckCircle,
          className: "bg-muted text-gray-600",
          label: "Unknown",
        }
    }
  }

  const config = getVarianceConfig()
  const Icon = config.icon

  return (
    <Badge className={cn("cursor-pointer hover:opacity-80 transition-opacity", config.className)} onClick={onClick}>
      <Icon className="w-3 h-3 mr-1" />
      {config.label}
    </Badge>
  )
}
