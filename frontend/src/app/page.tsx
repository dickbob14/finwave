"use client"

import React from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  ArrowRight, 
  BarChart3, 
  FileText, 
  Zap, 
  Shield, 
  TrendingUp,
  DollarSign,
  Users,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Database,
  PieChart
} from 'lucide-react'

const metrics = [
  { 
    title: "Total Revenue", 
    value: "$2.4M", 
    change: "+12.5%", 
    trend: "up",
    icon: DollarSign 
  },
  { 
    title: "Operating Expenses", 
    value: "$845K", 
    change: "-5.1%", 
    trend: "down",
    icon: Activity 
  },
  { 
    title: "Profit Margin", 
    value: "68.2%", 
    change: "+2.3%", 
    trend: "up",
    icon: TrendingUp 
  },
  { 
    title: "Active Users", 
    value: "2,847", 
    change: "+18%", 
    trend: "up",
    icon: Users 
  }
]

export default function HomePage() {
  const router = useRouter()
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <div className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-primary">Financial Dashboard</h1>
              <p className="text-sm text-muted-foreground mt-1">Real-time insights and analytics</p>
            </div>
            <div className="flex items-center gap-4">
              <Badge variant="secondary" className="bg-emerald-50 text-emerald-700 border-emerald-200">
                <Activity className="h-3 w-3 mr-1" />
                Live Data
              </Badge>
              <Button 
                variant="outline" 
                onClick={() => router.push('/templates')}
                className="hover:bg-gray-50"
              >
                View Reports
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="container mx-auto px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {metrics.map((metric, index) => {
            const Icon = metric.icon
            const isPositive = metric.trend === 'up'
            return (
              <Card key={index} className="hover:shadow-lg transition-shadow border-gray-200">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {metric.title}
                  </CardTitle>
                  <Icon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-primary mb-2">{metric.value}</div>
                  <div className="flex items-center">
                    <Badge 
                      variant="secondary"
                      className={`text-xs ${
                        isPositive 
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                          : 'bg-red-50 text-red-700 border-red-200'
                      }`}
                    >
                      {isPositive ? (
                        <ArrowUpRight className="h-3 w-3 mr-1" />
                      ) : (
                        <ArrowDownRight className="h-3 w-3 mr-1" />
                      )}
                      {metric.change}
                    </Badge>
                    <span className="text-xs text-muted-foreground ml-2">vs last month</span>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card className="hover:shadow-lg transition-shadow border-gray-200">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Revenue Trend</CardTitle>
                  <CardDescription>Monthly revenue performance</CardDescription>
                </div>
                <BarChart3 className="h-5 w-5 text-secondary" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] bg-gray-50 rounded-lg flex items-center justify-center">
                <p className="text-muted-foreground">Revenue chart visualization</p>
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow border-gray-200">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Expense Breakdown</CardTitle>
                  <CardDescription>By category</CardDescription>
                </div>
                <PieChart className="h-5 w-5 text-accent" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] bg-gray-50 rounded-lg flex items-center justify-center">
                <p className="text-muted-foreground">Expense chart visualization</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="hover:shadow-lg transition-shadow border-gray-200">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 bg-primary/10 rounded-lg flex items-center justify-center">
                  <FileText className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle className="text-base">Automated Reports</CardTitle>
                  <CardDescription className="text-xs">Board-ready in one click</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full hover:bg-gray-50" onClick={() => router.push('/templates')}>
                Generate Report
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow border-gray-200">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 bg-secondary/10 rounded-lg flex items-center justify-center">
                  <Database className="h-5 w-5 text-secondary" />
                </div>
                <div>
                  <CardTitle className="text-base">Data Sources</CardTitle>
                  <CardDescription className="text-xs">QuickBooks, Stripe, & more</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full hover:bg-gray-50" onClick={() => router.push('/settings')}>
                Manage Integrations
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow border-gray-200">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 bg-accent/10 rounded-lg flex items-center justify-center">
                  <Zap className="h-5 w-5 text-accent" />
                </div>
                <div>
                  <CardTitle className="text-base">AI Insights</CardTitle>
                  <CardDescription className="text-xs">Powered by GPT-4</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full hover:bg-gray-50" onClick={() => router.push('/ask')}>
                Ask AI Assistant
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}