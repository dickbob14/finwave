"use client"

/* eslint-disable @typescript-eslint/no-explicit-any */
import { useChart } from "@/lib/finwave"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import dynamic from "next/dynamic"
import { useMemo } from "react"

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => (
    <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-lg">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  ),
})

interface ChartProps {
  type: string
  title?: string
  description?: string
  className?: string
  chartSpec?: unknown // For direct chart data injection
}

export default function Chart({ 
  type, 
  title, 
  description, 
  className,
  chartSpec 
}: ChartProps) {
  const { chart, isLoading, isError } = useChart(type)
  
  // Use provided chartSpec or fetched chart data
  const chartData = useMemo(() => {
    if (chartSpec) return chartSpec
    return chart
  }, [chartSpec, chart])

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{title || `Loading ${type} chart...`}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (isError || !chartData) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{title || `${type} Chart`}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center bg-red-50 dark:bg-red-900/20 rounded-lg">
            <p className="text-red-600 dark:text-red-400">
              Failed to load chart data
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title || (chartData as any)?.title || "Chart"}</CardTitle>
        <CardDescription>
          {description || (chartData as any)?.ai_insight || (chartData as any)?.data_points ? `${(chartData as any).data_points} data points` : "Chart data"}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="w-full h-64">
          <Plot
            data={(chartData as any)?.plotly_data?.data || []}
            layout={{
              ...(chartData as any)?.plotly_data?.layout,
              autosize: true,
              margin: { t: 20, r: 20, b: 40, l: 60 },
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
              font: {
                size: 12,
              },
            }}
            config={{
              displayModeBar: false,
              responsive: true,
            }}
            useResizeHandler
            style={{ width: "100%", height: "100%" }}
          />
        </div>
      </CardContent>
    </Card>
  )
}