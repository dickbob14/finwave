"use client"

import type React from "react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, AlertTriangle, DollarSign, Users, BarChart3, Zap } from "lucide-react"

interface SuggestedQuestion {
  id: string
  question: string
  category: string
  icon: React.ComponentType<{ className?: string }>
  description: string
}

const suggestedQuestions: SuggestedQuestion[] = [
  {
    id: "1",
    question: "Why is our burn rate increasing this quarter?",
    category: "Cash Flow",
    icon: TrendingUp,
    description: "Analyze spending patterns across departments",
  },
  {
    id: "2",
    question: "What's driving the variance in our gross margin?",
    category: "Profitability",
    icon: BarChart3,
    description: "Compare actual vs budget performance",
  },
  {
    id: "3",
    question: "How is our sales pipeline affecting revenue forecasts?",
    category: "Revenue",
    icon: DollarSign,
    description: "Salesforce pipeline analysis",
  },
  {
    id: "4",
    question: "What's our current Rule of 40 score and how can we improve it?",
    category: "Growth",
    icon: Zap,
    description: "Growth rate + profit margin analysis",
  },
  {
    id: "5",
    question: "How does our headcount growth compare to revenue growth?",
    category: "Efficiency",
    icon: Users,
    description: "HR metrics from Gusto vs financial performance",
  },
  {
    id: "6",
    question: "Which expense categories are trending above budget?",
    category: "Expenses",
    icon: AlertTriangle,
    description: "QuickBooks expense analysis",
  },
]

interface SuggestedQuestionsProps {
  onQuestionSelect: (question: string) => void
}

export function SuggestedQuestions({ onQuestionSelect }: SuggestedQuestionsProps) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-primary mb-2">What would you like to know?</h2>
        <p className="text-muted-foreground">
          Ask questions about your financial data and get AI-powered insights from all your connected sources
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {suggestedQuestions.map((item) => {
          const Icon = item.icon
          return (
            <Card
              key={item.id}
              className="cursor-pointer hover:shadow-md transition-all hover:border-secondary/50"
              onClick={() => onQuestionSelect(item.question)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className="bg-secondary/10 p-2 rounded-lg">
                      <Icon className="h-4 w-4 text-secondary" />
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {item.category}
                    </Badge>
                  </div>
                </div>
                <CardTitle className="text-sm leading-tight">{item.question}</CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <CardDescription className="text-xs">{item.description}</CardDescription>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="text-center">
        <p className="text-sm text-muted-foreground">
          Or type your own question about revenue, expenses, cash flow, headcount, or any financial metric
        </p>
      </div>
    </div>
  )
}
