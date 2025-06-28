"use client"

import useSWR from "swr"
import { fetcher, apiPatch } from "@/lib/api"

export const useAlerts = (status?: string) => {
  const { data, error, isLoading, mutate } = useSWR(`/alerts${status ? `?status=${status}` : ""}`, fetcher)

  const acknowledgeAlert = async (alertId: string) => {
    await apiPatch(`/alerts/${alertId}`, { status: "acknowledged" })
    mutate()
  }

  return {
    alerts: data || [],
    isLoading,
    error,
    mutate,
    acknowledgeAlert,
  }
}
