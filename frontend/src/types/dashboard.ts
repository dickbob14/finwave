/**
 * Dashboard Types
 * Type definitions for the FinWave dashboard
 */

export interface DashboardSummary {
  company_name: string;
  last_sync: string;
  sync_status: 'success' | 'pending' | 'error';
  period: {
    start: string;
    end: string;
  };
  kpis: {
    revenue: KPIMetric;
    expenses: KPIMetric;
    net_profit: KPIMetric;
    cash_balance: KPIMetric;
    burn_rate: KPIMetric;
    runway_months: KPIMetric;
    gross_margin: KPIMetric;
    ebitda: KPIMetric;
    mrr: KPIMetric;
    arr: KPIMetric;
    customer_count: KPIMetric;
    cac: KPIMetric;
    ltv: KPIMetric;
    ltv_cac_ratio: KPIMetric;
    churn_rate: KPIMetric;
    working_capital: KPIMetric;
    current_ratio: KPIMetric;
    quick_ratio: KPIMetric;
    debt_to_equity: KPIMetric;
  };
  trends: {
    revenue_growth: number;
    expense_growth: number;
    customer_growth: number;
    cash_flow_trend: 'positive' | 'negative' | 'stable';
  };
  alerts: Alert[];
  ai_insights: string[];
}

export interface KPIMetric {
  value: number;
  formatted_value: string;
  change_percent: number;
  change_value: number;
  trend: 'up' | 'down' | 'stable';
  status: 'good' | 'warning' | 'critical';
  sparkline?: number[];
}

export interface Alert {
  id: string;
  type: 'warning' | 'critical' | 'info';
  title: string;
  message: string;
  metric?: string;
  created_at: string;
}

export interface CashFlowData {
  periods: string[];
  cash_in: number[];
  cash_out: number[];
  net_cash_flow: number[];
  cumulative_cash: number[];
  forecast?: {
    periods: string[];
    projected_cash_flow: number[];
    projected_balance: number[];
    confidence_interval: {
      lower: number[];
      upper: number[];
    };
  };
}

export interface RevenueAnalysis {
  by_period: {
    periods: string[];
    revenue: number[];
    recurring: number[];
    non_recurring: number[];
  };
  by_customer: {
    name: string;
    revenue: number;
    percentage: number;
  }[];
  by_product: {
    name: string;
    revenue: number;
    percentage: number;
  }[];
  growth_metrics: {
    mom_growth: number[];
    yoy_growth: number[];
    cagr: number;
  };
}

export interface ExpenseAnalysis {
  by_category: {
    category: string;
    amount: number;
    percentage: number;
    trend: 'up' | 'down' | 'stable';
  }[];
  by_vendor: {
    name: string;
    amount: number;
    percentage: number;
  }[];
  trends: {
    periods: string[];
    operating_expenses: number[];
    cost_of_goods: number[];
    salaries: number[];
    marketing: number[];
    other: number[];
  };
}

export interface CustomerMetrics {
  acquisition: {
    periods: string[];
    new_customers: number[];
    cac_trend: number[];
  };
  retention: {
    cohorts: {
      month: string;
      retention_curve: number[];
    }[];
    average_ltv: number;
    churn_by_month: number[];
  };
  revenue_distribution: {
    buckets: {
      range: string;
      count: number;
      revenue: number;
    }[];
  };
}

export interface FinancialHealth {
  liquidity: {
    working_capital: number;
    current_ratio: number;
    quick_ratio: number;
    days_sales_outstanding: number;
    days_payables_outstanding: number;
  };
  profitability: {
    gross_margin: number;
    operating_margin: number;
    net_margin: number;
    ebitda_margin: number;
  };
  leverage: {
    debt_to_equity: number;
    debt_to_assets: number;
    interest_coverage: number;
  };
  efficiency: {
    asset_turnover: number;
    inventory_turnover: number;
    receivables_turnover: number;
  };
}