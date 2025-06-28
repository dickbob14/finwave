"use client"

import useSWR from "swr"
import { fetcher } from "@/lib/api"

export const useMetrics = (workspace: string) => {
  const { data, error, isLoading, mutate } = useSWR(workspace ? `/metrics/${workspace}/metrics/summary` : null, fetcher)

  return {
    // Summary of metrics for selected period
    summary: data?.metrics || {},
    // ISO date for the summary period
    period: data?.period,
    // Workspace identifier
    workspaceId: data?.workspace_id,
    isLoading,
    error,
    mutate,
  }
}

export const useMetricTimeseries = (workspace: string, metricId: string, periods = 12) => {
  const { data, error, isLoading, mutate } = useSWR(
    workspace && metricId ? `/metrics/${workspace}/timeseries?metric_id=${metricId}&periods=${periods}` : null,
    fetcher,
  )

  return {
    timeseries: data,
    isLoading,
    error,
    mutate,
  }
}
