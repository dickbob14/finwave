"use client"

import useSWR from "swr"
import { fetcher } from "@/lib/api"

export const useTemplates = () => {
  const { data, error, isLoading, mutate } = useSWR("/templates", fetcher)

  return {
    templates: data || [],
    isLoading,
    error,
    mutate,
  }
}

export const useTemplateSnapshot = (templateName: string) => {
  const { data, error, isLoading, mutate } = useSWR(
    templateName ? `/templates/${templateName}/snapshot` : null,
    fetcher,
  )

  return {
    snapshot: data,
    isLoading,
    error,
    mutate,
  }
}
