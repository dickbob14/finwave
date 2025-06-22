import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import DashboardPage from '@/app/dashboard/page'

// Mock SWR to avoid API calls in tests
jest.mock('swr', () => ({
  __esModule: true,
  default: () => ({
    data: {
      key_metrics: {
        total_transactions: 768,
        revenue_trend: "Growing 12% month-over-month",
        expense_ratio: "68% of revenue",
        cash_flow: "Positive with seasonal patterns"
      },
      ai_recommendations: [
        "Focus on accounts receivable collection",
        "Consider seasonal cash flow planning"
      ],
      variance_alerts: [
        "Office expenses 15% above budget",
        "Service revenue outperforming projections"
      ]
    },
    error: null,
    isLoading: false
  })
}))

// Mock our API hooks
jest.mock('@/lib/finwave', () => ({
  useInsights: () => ({
    insights: {
      key_metrics: {
        total_transactions: 768,
        revenue_trend: "Growing 12% month-over-month",
        expense_ratio: "68% of revenue",
        cash_flow: "Positive with seasonal patterns"
      },
      ai_recommendations: [
        "Focus on accounts receivable collection",
        "Consider seasonal cash flow planning"
      ],
      variance_alerts: [
        "Office expenses 15% above budget",
        "Service revenue outperforming projections"
      ]
    },
    isLoading: false,
    isError: null
  }),
  useChart: () => ({
    chart: {
      title: "Revenue Trend",
      plotly_data: {
        data: [],
        layout: {}
      },
      ai_insight: "Mock chart data"
    },
    isLoading: false,
    isError: null
  }),
  askAI: jest.fn()
}))

// Mock dynamic imports
jest.mock('next/dynamic', () => () => {
  const DynamicComponent = () => <div data-testid="chart-placeholder">Chart Loading...</div>
  DynamicComponent.displayName = 'Chart'
  return DynamicComponent
})

describe('Dashboard Page', () => {
  it('renders dashboard with KPI tiles', async () => {
    render(<DashboardPage />)
    
    // Check for main heading
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    
    // Check for Revenue KPI tile (using getAllByText since there are multiple instances)
    expect(screen.getAllByText('Revenue Trend')).toHaveLength(2)
    expect(screen.getByText(/Growing 12% month-over-month/)).toBeInTheDocument()
    
    // Check for transaction count
    expect(screen.getByText('768')).toBeInTheDocument()
    
    // Check for AI insights button
    expect(screen.getByText('Get AI Insights')).toBeInTheDocument()
  })

  it('displays AI recommendations', () => {
    render(<DashboardPage />)
    
    expect(screen.getByText('AI Recommendations')).toBeInTheDocument()
    expect(screen.getByText(/Focus on accounts receivable collection/)).toBeInTheDocument()
  })

  it('displays variance alerts', () => {
    render(<DashboardPage />)
    
    expect(screen.getByText('Variance Alerts')).toBeInTheDocument()
    expect(screen.getByText(/Office expenses 15% above budget/)).toBeInTheDocument()
  })
})