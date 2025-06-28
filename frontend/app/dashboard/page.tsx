"use client"

import React, { useMemo } from "react"
import { useMetrics, useMetricTimeseries } from "@/hooks/useMetrics"
import { KpiCardWithVariance } from "@/components/KpiCardWithVariance"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from "recharts"
import { Sparklines, SparklinesLine, SparklinesSpots } from "react-sparklines"
import { motion } from "framer-motion"
import { 
  TrendingUp, TrendingDown, AlertCircle, CheckCircle, 
  DollarSign, Users, ShoppingCart, Activity,
  ArrowUpRight, ArrowDownRight, Minus
} from "lucide-react"

// Helper to format metric values based on unit
const formatValue = (value: number, unit?: string) => {
  if (unit === "dollars") {
    return value.toLocaleString(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
  }
  if (unit === "percentage") {
    // API returns decimal (e.g. 0.12 for 12%) or already percentage
    const pct = value > 1 ? value : value * 100
    return `${pct.toFixed(1)}%`
  }
  return value.toLocaleString()
}

// Demo data generation
const generateDemoData = () => {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const currentMonth = new Date().getMonth()
  
  return {
    revenue: months.slice(0, currentMonth + 1).map((month, i) => ({
      month,
      value: 450000 + Math.random() * 100000 + (i * 15000),
      target: 450000 + (i * 18000)
    })),
    expenses: months.slice(0, currentMonth + 1).map((month, i) => ({
      month,
      value: 380000 + Math.random() * 80000 + (i * 12000),
      budget: 400000 + (i * 14000)
    })),
    cashflow: months.slice(0, currentMonth + 1).map((month, i) => ({
      month,
      inflow: 450000 + Math.random() * 100000 + (i * 15000),
      outflow: 380000 + Math.random() * 80000 + (i * 12000)
    })),
    categoryBreakdown: [
      { name: 'Sales Revenue', value: 65, color: '#10b981' },
      { name: 'Service Revenue', value: 25, color: '#3b82f6' },
      { name: 'Other Income', value: 10, color: '#8b5cf6' }
    ]
  }
}

// Metric icons mapping
const metricIcons = {
  revenue: DollarSign,
  customers: Users,
  orders: ShoppingCart,
  growth: Activity
}

// Variance calculation
const calculateVariance = (current: number, previous: number) => {
  const variance = ((current - previous) / previous) * 100
  return {
    value: variance,
    trend: variance > 0 ? "up" : variance < 0 ? "down" : "neutral",
    status: Math.abs(variance) > 10 ? "critical" : Math.abs(variance) > 5 ? "warning" : "none"
  }
}

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
}

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 100
    }
  }
}

export default function DashboardPage() {
  // TODO: Replace 'default' with actual workspace ID from context/auth
  const workspace = 'default'
  const { summary, period, isLoading, error } = useMetrics(workspace)
  
  // Generate demo data
  const demoData = useMemo(() => generateDemoData(), [])
  
  // Calculate some demo metrics if no real data
  const metrics = useMemo(() => {
    if (summary && Object.keys(summary).length > 0) {
      return summary
    }
    
    // Demo metrics
    return {
      revenue: { 
        value: 567890, 
        unit: 'dollars', 
        display_name: 'Total Revenue',
        previous: 520000
      },
      expenses: { 
        value: 432100, 
        unit: 'dollars', 
        display_name: 'Total Expenses',
        previous: 410000
      },
      profit_margin: { 
        value: 0.238, 
        unit: 'percentage', 
        display_name: 'Profit Margin',
        previous: 0.21
      },
      customer_count: { 
        value: 1847, 
        unit: 'count', 
        display_name: 'Active Customers',
        previous: 1720
      }
    }
  }, [summary])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="p-8">
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>Error loading metrics: {error.message}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <motion.div 
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold text-primary">Financial Dashboard</h1>
        {period && <p className="text-muted-foreground mt-1">As of {new Date(period).toLocaleDateString()}</p>}
      </motion.div>

      {/* KPI Cards */}
      <motion.div 
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
        variants={itemVariants}
      >
        {Object.entries(metrics).map(([metricId, metric]) => {
          const variance = metric.previous 
            ? calculateVariance(metric.value, metric.previous)
            : { value: 0, trend: "neutral" as const, status: "none" as const }
          
          return (
            <KpiCardWithVariance
              key={metricId}
              title={metric.display_name}
              value={formatValue(metric.value, metric.unit)}
              trend={variance.trend}
              trendValue={variance.value !== 0 ? `${variance.value > 0 ? '+' : ''}${variance.value.toFixed(1)}%` : undefined}
              variance={variance.status}
              metricId={metricId}
            />
          )
        })}
      </motion.div>

      {/* Charts Section */}
      <motion.div variants={itemVariants}>
        <Tabs defaultValue="revenue" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:inline-grid">
            <TabsTrigger value="revenue">Revenue</TabsTrigger>
            <TabsTrigger value="expenses">Expenses</TabsTrigger>
            <TabsTrigger value="cashflow">Cash Flow</TabsTrigger>
            <TabsTrigger value="breakdown">Breakdown</TabsTrigger>
          </TabsList>

          <TabsContent value="revenue" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Revenue Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={demoData.revenue}>
                    <defs>
                      <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(value: number) => `$${value.toLocaleString()}`} />
                    <Legend />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#10b981" 
                      fillOpacity={1} 
                      fill="url(#colorRevenue)" 
                      name="Actual"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="target" 
                      stroke="#6b7280" 
                      strokeDasharray="5 5" 
                      name="Target"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="expenses" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Expenses vs Budget</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={demoData.expenses}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(value: number) => `$${value.toLocaleString()}`} />
                    <Legend />
                    <Bar dataKey="value" fill="#ef4444" name="Actual" />
                    <Bar dataKey="budget" fill="#fbbf24" name="Budget" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="cashflow" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Cash Flow Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={demoData.cashflow}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(value: number) => `$${value.toLocaleString()}`} />
                    <Legend />
                    <Line type="monotone" dataKey="inflow" stroke="#10b981" strokeWidth={2} name="Inflow" />
                    <Line type="monotone" dataKey="outflow" stroke="#ef4444" strokeWidth={2} name="Outflow" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="breakdown" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Revenue Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={demoData.categoryBreakdown}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ${value}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {demoData.categoryBreakdown.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Performance Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Revenue Target</span>
                      <span>85%</span>
                    </div>
                    <Progress value={85} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Expense Control</span>
                      <span>92%</span>
                    </div>
                    <Progress value={92} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Profit Margin</span>
                      <span>73%</span>
                    </div>
                    <Progress value={73} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Customer Growth</span>
                      <span>68%</span>
                    </div>
                    <Progress value={68} className="h-2" />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </motion.div>

      {/* Quick Stats */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle>Quick Stats</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Revenue Sparkline</p>
                <Sparklines data={[45, 52, 48, 56, 61, 58, 63, 60, 66, 71, 68, 75]} height={60}>
                  <SparklinesLine color="#10b981" />
                  <SparklinesSpots />
                </Sparklines>
              </div>
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Expense Sparkline</p>
                <Sparklines data={[38, 40, 37, 42, 41, 39, 43, 45, 44, 46, 45, 48]} height={60}>
                  <SparklinesLine color="#ef4444" />
                  <SparklinesSpots />
                </Sparklines>
              </div>
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Profit Sparkline</p>
                <Sparklines data={[7, 12, 11, 14, 20, 19, 20, 15, 22, 25, 23, 27]} height={60}>
                  <SparklinesLine color="#3b82f6" />
                  <SparklinesSpots />
                </Sparklines>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Alerts Section */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <AlertCircle className="h-5 w-5 text-warning mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Expense Variance Alert</p>
                  <p className="text-sm text-muted-foreground">Marketing expenses exceeded budget by 15% this month</p>
                </div>
                <span className="text-xs text-muted-foreground">2h ago</span>
              </div>
              <div className="flex items-start space-x-3">
                <CheckCircle className="h-5 w-5 text-success mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Revenue Target Met</p>
                  <p className="text-sm text-muted-foreground">Q3 revenue target achieved with 102% completion</p>
                </div>
                <span className="text-xs text-muted-foreground">1d ago</span>
              </div>
              <div className="flex items-start space-x-3">
                <TrendingUp className="h-5 w-5 text-primary mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Positive Cash Flow Trend</p>
                  <p className="text-sm text-muted-foreground">Cash flow improved by 8% compared to last quarter</p>
                </div>
                <span className="text-xs text-muted-foreground">3d ago</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}