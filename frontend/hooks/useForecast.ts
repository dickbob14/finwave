"use client"

import useSWR from "swr"
import { fetcher, apiPut } from "@/lib/api"

export const useForecastDrivers = () => {
  const { data, error, isLoading, mutate } = useSWR("/forecast/drivers", fetcher)

  const updateDriver = async (driverId: string, value: number) => {
    await apiPut(`/forecast/drivers/${driverId}`, { value })
    mutate()
  }

  return {
    drivers: data || [],
    isLoading,
    error,
    mutate,
    updateDriver,
  }
}

export const useForecastComparison = (base?: string, other?: string) => {
  const { data, error, isLoading, mutate } = useSWR(
    base && other ? `/forecast/scenarios/compare?base=${base}&other=${other}` : null,
    fetcher,
  )

  return {
    comparison: data,
    isLoading,
    error,
    mutate,
  }
}
