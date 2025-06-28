/**
 * Dashboard Hooks
 * Custom hooks for fetching and managing dashboard data
 */

import useSWR from 'swr';
import { useCallback } from 'react';
import type {
  DashboardSummary,
  CashFlowData,
  RevenueAnalysis,
  ExpenseAnalysis,
  CustomerMetrics,
  FinancialHealth
} from '@/types/dashboard';

const API_BASE_URL = process.env.NEXT_PUBLIC_FINWAVE_API_URL || 'http://localhost:8000';

// Base fetcher with auth
const fetcher = async (url: string) => {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    headers: {
      'Authorization': 'Bearer demo-token',
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = new Error('An error occurred while fetching the data.');
    throw error;
  }

  return response.json();
};

// Dashboard summary hook
export function useDashboardSummary(companyId: string = 'default') {
  const { data, error, isLoading, mutate } = useSWR<DashboardSummary>(
    `/api/${companyId}/dashboard/data`,
    fetcher,
    {
      refreshInterval: 30000, // Refresh every 30 seconds
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
    }
  );

  return {
    dashboard: data,
    isLoading,
    isError: error,
    refresh: mutate,
  };
}

// Cash flow data hook
export function useCashFlow(companyId: string = 'default') {
  const { data, error, isLoading } = useSWR<CashFlowData>(
    `/api/dashboard/${companyId}/cash-flow`,
    fetcher,
    {
      refreshInterval: 60000, // Refresh every minute
    }
  );

  return {
    cashFlow: data,
    isLoading,
    isError: error,
  };
}

// Revenue analysis hook
export function useRevenueAnalysis(companyId: string = 'default') {
  const { data, error, isLoading } = useSWR<RevenueAnalysis>(
    `/api/dashboard/${companyId}/revenue-analysis`,
    fetcher,
    {
      refreshInterval: 60000,
    }
  );

  return {
    revenue: data,
    isLoading,
    isError: error,
  };
}

// Expense analysis hook
export function useExpenseAnalysis(companyId: string = 'default') {
  const { data, error, isLoading } = useSWR<ExpenseAnalysis>(
    `/api/dashboard/${companyId}/expense-analysis`,
    fetcher,
    {
      refreshInterval: 60000,
    }
  );

  return {
    expenses: data,
    isLoading,
    isError: error,
  };
}

// Customer metrics hook
export function useCustomerMetrics(companyId: string = 'default') {
  const { data, error, isLoading } = useSWR<CustomerMetrics>(
    `/api/dashboard/${companyId}/customer-metrics`,
    fetcher,
    {
      refreshInterval: 300000, // Refresh every 5 minutes
    }
  );

  return {
    customers: data,
    isLoading,
    isError: error,
  };
}

// Financial health hook
export function useFinancialHealth(companyId: string = 'default') {
  const { data, error, isLoading } = useSWR<FinancialHealth>(
    `/api/dashboard/${companyId}/financial-health`,
    fetcher,
    {
      refreshInterval: 300000,
    }
  );

  return {
    health: data,
    isLoading,
    isError: error,
  };
}

// Trigger sync hook
export function useSyncQuickBooks(companyId: string = 'default') {
  const triggerSync = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/dashboard/${companyId}/sync`, {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer demo-token',
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Sync failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Sync error:', error);
      throw error;
    }
  }, [companyId]);

  return { triggerSync };
}

// Combined dashboard data hook
export function useDashboard(companyId: string = 'default') {
  const { dashboard, isLoading: summaryLoading, refresh } = useDashboardSummary(companyId);
  const { cashFlow, isLoading: cashFlowLoading } = useCashFlow(companyId);
  const { revenue, isLoading: revenueLoading } = useRevenueAnalysis(companyId);
  const { expenses, isLoading: expenseLoading } = useExpenseAnalysis(companyId);
  const { triggerSync } = useSyncQuickBooks(companyId);

  const isLoading = summaryLoading || cashFlowLoading || revenueLoading || expenseLoading;

  return {
    dashboard,
    cashFlow,
    revenue,
    expenses,
    isLoading,
    refresh,
    triggerSync,
  };
}