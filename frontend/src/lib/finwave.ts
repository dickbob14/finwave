/**
 * FinWave API Client
 * Auto-generated typed fetchers for the FinWave backend
 */

import useSWR from 'swr';

const API_BASE_URL = process.env.NEXT_PUBLIC_FINWAVE_API_URL || 'http://localhost:8000';

// Types for API responses
export interface HealthResponse {
  status: string;
  openai: string;
  quickbooks: string;
  database: string;
  test_data: string;
  ai_capabilities: string[];
}

export interface AskRequest {
  query: string;
}

export interface AskResponse {
  query: string;
  ai_analysis: string;
  data_context: {
    transactions: number;
    period: string;
    accounts: number;
    customers: number;
    vendors: number;
  };
  powered_by: string;
  timestamp: string;
}

export interface InsightsResponse {
  summary: string;
  key_metrics: {
    total_transactions?: number;
    revenue_trend?: string;
    expense_ratio?: string;
    cash_flow?: string;
    total_revenue?: string;
    total_expenses?: string;
    net_profit?: string;
    profit_margin?: string;
    accounts_receivable?: string;
    outstanding_invoices?: number;
  };
  ai_recommendations: string[];
  variance_alerts: string[];
  generated_by: string;
  data_source?: string;
}

export interface ChartResponse {
  chart_type: string;
  title: string;
  plotly_data: {
    data: unknown[];
    layout: unknown;
  };
  data_points: number;
  ai_insight: string;
  generated_at: string;
}

// Base fetcher function
const fetcher = async (url: string) => {
  const response = await fetch(`${API_BASE_URL}${url}`);
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  return response.json();
};

// POST fetcher for mutations
const postFetcher = async ({ url, data }: { url: string; data: unknown }) => {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  return response.json();
};

// Hooks for data fetching
export function useHealth() {
  const { data, error, isLoading, mutate } = useSWR<HealthResponse>('/health', fetcher, {
    revalidateOnFocus: false,
    onError: (err) => console.error('Health fetch error:', err),
  });
  return {
    health: data,
    isLoading,
    isError: error,
    mutate,
  };
}

export function useInsights() {
  const { data, error, isLoading, mutate } = useSWR<InsightsResponse>('/real/insights', fetcher, {
    revalidateOnFocus: false,
    onError: (err) => console.error('Insights fetch error:', err),
  });
  return {
    insights: data,
    isLoading,
    isError: error,
    mutate,
  };
}

export function useChart(type: string) {
  const { data, error, isLoading, mutate } = useSWR<ChartResponse>(
    type ? `/real/charts/${type}` : null,
    fetcher,
    {
      revalidateOnFocus: false,
      onError: (err) => console.error('Chart fetch error:', err),
    }
  );
  return {
    chart: data,
    isLoading,
    isError: error,
    mutate,
  };
}

// Mutation hook for AI queries
export async function askAI(query: string): Promise<AskResponse> {
  return postFetcher({
    url: '/ask',
    data: { query },
  });
}

// Utility functions
export const finwaveApi = {
  health: () => fetcher('/health'),
  insights: () => fetcher('/real/insights'),
  chart: (type: string) => fetcher(`/real/charts/${type}`),
  ask: (query: string) => postFetcher({ url: '/ask', data: { query } }),
  connectQB: () => fetcher('/connect_qb'),
  transactions: () => fetcher('/real/transactions'),
  company: () => fetcher('/real/company'),
};