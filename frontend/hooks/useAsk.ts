"use client"

import { useState, useCallback } from "react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  citations?: Citation[]
  sql?: string
  kpis?: KPI[]
  timestamp: Date
}

interface Citation {
  id: string
  source: string
  snippet: string
  url?: string
  type?: "sql" | "document" | "api" | "metric"
}

interface KPI {
  metric: string
  value: string
  change: string
  trend: "up" | "down" | "neutral"
  period?: string
}

export function useAsk() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  const generateMockResponse = (query: string): Message => {
    const responses = {
      burn: {
        content:
          "Your burn rate increased 23% this quarter to $485K/month, primarily driven by headcount expansion (+$180K) and increased marketing spend (+$95K). The engineering team grew from 12 to 18 people [1], while marketing campaigns for the new product launch increased ad spend by 40% [2]. However, this aligns with your growth strategy as revenue also increased 31% [3].",
        citations: [
          {
            id: "1",
            source: "Gusto Payroll",
            snippet:
              "Engineering headcount: Jan: 12 → Mar: 18 employees. Average salary: $145K. Total monthly cost increase: $72K → $217K",
            type: "api",
          },
          {
            id: "2",
            source: "QuickBooks Expenses",
            snippet:
              "Marketing expenses Q1: $67K → $162K. Primary drivers: Google Ads (+$45K), Content marketing (+$28K), Events (+$22K)",
            type: "api",
          },
          {
            id: "3",
            source: "Revenue Analysis",
            snippet: "Q1 Revenue: $1.2M vs Q4: $915K. MRR growth: 31% QoQ. New customer acquisition: +47 accounts",
            type: "metric",
          },
        ],
        kpis: [
          { metric: "Monthly Burn Rate", value: "$485K", change: "+23%", trend: "up" as const, period: "March 2024" },
          { metric: "Headcount", value: "43", change: "+14%", trend: "up" as const, period: "Q1 2024" },
          { metric: "Revenue Growth", value: "31%", change: "+8pp", trend: "up" as const, period: "QoQ" },
          { metric: "Runway", value: "18 months", change: "-3 months", trend: "down" as const, period: "Current cash" },
        ],
        sql: `SELECT 
  DATE_TRUNC('month', date) as month,
  SUM(amount) as monthly_burn,
  LAG(SUM(amount)) OVER (ORDER BY DATE_TRUNC('month', date)) as prev_month,
  (SUM(amount) - LAG(SUM(amount)) OVER (ORDER BY DATE_TRUNC('month', date))) / LAG(SUM(amount)) OVER (ORDER BY DATE_TRUNC('month', date)) * 100 as growth_rate
FROM expenses 
WHERE category IN ('payroll', 'marketing', 'operations')
  AND date >= '2024-01-01'
GROUP BY DATE_TRUNC('month', date)
ORDER BY month DESC;`,
      },
      margin: {
        content:
          "Your gross margin declined 4.2pp to 68.3% this quarter due to increased COGS from new product features and higher cloud infrastructure costs. The main drivers are: 1) AWS costs up 45% due to new AI features [1], 2) Third-party API costs increased with usage [2], and 3) Customer success team expansion to support growth [3].",
        citations: [
          {
            id: "1",
            source: "QuickBooks - AWS",
            snippet:
              "AWS monthly costs: Jan $12K → Mar $17.4K. Primary increase: GPU instances for AI model training (+$3.8K), increased data storage (+$1.6K)",
            type: "api",
          },
          {
            id: "2",
            source: "API Costs Analysis",
            snippet:
              "Third-party API costs: OpenAI $8.2K, Stripe processing $4.1K, Twilio $2.3K. 35% increase vs Q4 due to higher usage",
            type: "metric",
          },
        ],
        kpis: [
          { metric: "Gross Margin", value: "68.3%", change: "-4.2pp", trend: "down" as const },
          { metric: "COGS", value: "$387K", change: "+28%", trend: "up" as const },
          { metric: "Infrastructure Costs", value: "$52K", change: "+45%", trend: "up" as const },
        ],
      },
      pipeline: {
        content:
          "Your sales pipeline is strong with $2.4M in qualified opportunities, up 67% from last quarter. The pipeline suggests 23% revenue growth next quarter based on historical conversion rates [1]. Key insights: Enterprise deals (>$50K ARR) now represent 45% of pipeline value [2], and average deal size increased to $28K ARR [3].",
        citations: [
          {
            id: "1",
            source: "Salesforce Pipeline",
            snippet:
              "Total pipeline value: $2.4M across 47 opportunities. Stage breakdown: Discovery (32%), Proposal (28%), Negotiation (23%), Closed-Won probability: 67%",
            type: "api",
          },
          {
            id: "2",
            source: "Deal Size Analysis",
            snippet:
              "Enterprise deals (>$50K): 12 opportunities worth $1.08M. SMB deals (<$50K): 35 opportunities worth $1.32M",
            type: "metric",
          },
        ],
        kpis: [
          { metric: "Pipeline Value", value: "$2.4M", change: "+67%", trend: "up" as const },
          { metric: "Avg Deal Size", value: "$28K", change: "+15%", trend: "up" as const },
          { metric: "Win Rate", value: "67%", change: "+5pp", trend: "up" as const },
          { metric: "Sales Cycle", value: "89 days", change: "-12 days", trend: "down" as const },
        ],
      },
      rule: {
        content:
          "Your current Rule of 40 score is 47%, which is excellent for a growth-stage SaaS company. This combines 31% revenue growth + 16% EBITDA margin [1]. To improve further, focus on: 1) Optimizing customer acquisition cost (currently $2,400) [2], 2) Increasing net revenue retention (currently 118%) [3], and 3) Improving gross margin efficiency.",
        citations: [
          {
            id: "1",
            source: "Financial Metrics",
            snippet: "Q1 2024: Revenue growth 31% YoY, EBITDA margin 16%. Rule of 40 calculation: 31% + 16% = 47%",
            type: "metric",
          },
          {
            id: "2",
            source: "CAC Analysis",
            snippet:
              "Customer Acquisition Cost: $2,400 (Sales & Marketing spend / New customers). Industry benchmark: $1,800-$2,200",
            type: "metric",
          },
        ],
        kpis: [
          { metric: "Rule of 40", value: "47%", change: "+3pp", trend: "up" as const },
          { metric: "Revenue Growth", value: "31%", change: "+2pp", trend: "up" as const },
          { metric: "EBITDA Margin", value: "16%", change: "+1pp", trend: "up" as const },
          { metric: "NRR", value: "118%", change: "+3pp", trend: "up" as const },
        ],
      },
    }

    // Simple keyword matching for demo
    const key = Object.keys(responses).find((k) => query.toLowerCase().includes(k))
    return {
      id: Date.now().toString(),
      role: "assistant",
      timestamp: new Date(),
      ...(key
        ? responses[key as keyof typeof responses]
        : {
            content:
              "I understand you're asking about your financial data. Based on your connected sources (QuickBooks, Salesforce, Gusto), I can help analyze revenue trends, expense patterns, cash flow, and key metrics. Could you be more specific about what you'd like to know?",
            citations: [],
          }),
    }
  }

  const sendMessage = useCallback(async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setIsStreaming(true)

    try {
      // Call the real backend API
      const response = await fetch('/api/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer demo-token'
        },
        body: JSON.stringify({ query: content })
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()
      
      // Format the response as a message
      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: data.message || data.error || JSON.stringify(data),
        timestamp: new Date(),
        citations: data.citations || [],
        sql: data.sql,
        kpis: data.kpis || []
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error calling ask API:', error)
      // Fall back to mock response if API fails
      const assistantMessage = generateMockResponse(content)
      setMessages((prev) => [...prev, assistantMessage])
    } finally {
      setIsStreaming(false)
    }
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    isStreaming,
    sendMessage,
    clearMessages,
  }
}
