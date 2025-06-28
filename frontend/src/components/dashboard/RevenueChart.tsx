/**
 * RevenueChart Component
 * Revenue trends visualization with growth metrics
 */

import { motion } from 'framer-motion';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
  ComposedChart,
  Cell,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TrendingUp, DollarSign, Users, Package } from 'lucide-react';
import type { RevenueAnalysis } from '@/types/dashboard';
import { cn } from '@/lib/utils';

interface RevenueChartProps {
  data: RevenueAnalysis;
  loading?: boolean;
}

const COLORS = ['#2db3a6', '#5b5bf2', '#f97316', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#3b82f6'];

export function RevenueChart({ data, loading = false }: RevenueChartProps) {
  if (loading) {
    return (
      <Card className="animate-pulse">
        <CardHeader>
          <div className="h-6 bg-slate-200 rounded w-1/3"></div>
        </CardHeader>
        <CardContent>
          <div className="h-64 bg-slate-100 rounded"></div>
        </CardContent>
      </Card>
    );
  }

  // Prepare time series data
  const timeSeriesData = data.by_period.periods.map((period, index) => ({
    period,
    total: data.by_period.revenue[index],
    recurring: data.by_period.recurring[index],
    nonRecurring: data.by_period.non_recurring[index],
    growth: data.growth_metrics.mom_growth[index],
  }));

  // Calculate key metrics
  const totalRevenue = data.by_period.revenue.reduce((a, b) => a + b, 0);
  const recurringPercentage = (data.by_period.recurring.reduce((a, b) => a + b, 0) / totalRevenue) * 100;
  const avgGrowth = data.growth_metrics.mom_growth.reduce((a, b) => a + b, 0) / data.growth_metrics.mom_growth.length;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 rounded-lg shadow-lg border border-slate-200">
          <p className="font-semibold text-sm mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between gap-4 text-sm">
              <span className="flex items-center gap-1">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                {entry.name}
              </span>
              <span className="font-medium">
                {entry.name === 'Growth' 
                  ? `${entry.value.toFixed(1)}%`
                  : `$${entry.value.toLocaleString()}`
                }
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="overflow-hidden">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg font-semibold">Revenue Analysis</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Revenue trends and composition
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm text-muted-foreground">MoM Growth</p>
                <p className={cn(
                  "text-lg font-semibold",
                  avgGrowth >= 0 ? "text-green-600" : "text-red-600"
                )}>
                  {avgGrowth >= 0 ? '+' : ''}{avgGrowth.toFixed(1)}%
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Recurring</p>
                <p className="text-lg font-semibold text-slate-900">
                  {recurringPercentage.toFixed(0)}%
                </p>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="trends" className="space-y-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="trends">Trends</TabsTrigger>
              <TabsTrigger value="customers">By Customer</TabsTrigger>
              <TabsTrigger value="products">By Product</TabsTrigger>
            </TabsList>

            <TabsContent value="trends" className="space-y-4">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart
                    data={timeSeriesData}
                    margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                  >
                    <defs>
                      <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#2db3a6" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="#2db3a6" stopOpacity={0.1} />
                      </linearGradient>
                      <linearGradient id="recurringGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#5b5bf2" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="#5b5bf2" stopOpacity={0.1} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                    <XAxis
                      dataKey="period"
                      className="text-xs"
                      tick={{ fill: '#64748b' }}
                      axisLine={{ stroke: '#e2e8f0' }}
                    />
                    <YAxis
                      yAxisId="left"
                      className="text-xs"
                      tick={{ fill: '#64748b' }}
                      axisLine={{ stroke: '#e2e8f0' }}
                      tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                    />
                    <YAxis
                      yAxisId="right"
                      orientation="right"
                      className="text-xs"
                      tick={{ fill: '#64748b' }}
                      axisLine={{ stroke: '#e2e8f0' }}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend
                      verticalAlign="top"
                      height={36}
                      iconType="circle"
                      wrapperStyle={{ fontSize: '12px' }}
                    />
                    <Area
                      yAxisId="left"
                      type="monotone"
                      dataKey="total"
                      name="Total Revenue"
                      stroke="#2db3a6"
                      strokeWidth={2}
                      fill="url(#revenueGradient)"
                    />
                    <Area
                      yAxisId="left"
                      type="monotone"
                      dataKey="recurring"
                      name="Recurring"
                      stroke="#5b5bf2"
                      strokeWidth={2}
                      fill="url(#recurringGradient)"
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="growth"
                      name="Growth"
                      stroke="#f97316"
                      strokeWidth={2}
                      dot={{ fill: '#f97316', r: 4 }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </TabsContent>

            <TabsContent value="customers" className="space-y-4">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data.by_customer.slice(0, 10)}
                    layout="vertical"
                    margin={{ top: 10, right: 10, left: 80, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                    <XAxis
                      type="number"
                      className="text-xs"
                      tick={{ fill: '#64748b' }}
                      axisLine={{ stroke: '#e2e8f0' }}
                      tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                    />
                    <YAxis
                      dataKey="name"
                      type="category"
                      className="text-xs"
                      tick={{ fill: '#64748b' }}
                      axisLine={{ stroke: '#e2e8f0' }}
                      width={75}
                    />
                    <Tooltip
                      formatter={(value: any) => `$${value.toLocaleString()}`}
                    />
                    <Bar dataKey="revenue" radius={[0, 4, 4, 0]}>
                      {data.by_customer.slice(0, 10).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-slate-50">
                  <p className="text-sm text-muted-foreground">Top Customer</p>
                  <p className="font-semibold">{data.by_customer[0]?.name}</p>
                  <p className="text-sm text-slate-600">
                    ${data.by_customer[0]?.revenue.toLocaleString()} ({data.by_customer[0]?.percentage.toFixed(1)}%)
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-slate-50">
                  <p className="text-sm text-muted-foreground">Customer Concentration</p>
                  <p className="font-semibold">
                    Top 5: {data.by_customer.slice(0, 5).reduce((acc, c) => acc + c.percentage, 0).toFixed(0)}%
                  </p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="products" className="space-y-4">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data.by_product.slice(0, 10)}
                    layout="vertical"
                    margin={{ top: 10, right: 10, left: 80, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                    <XAxis
                      type="number"
                      className="text-xs"
                      tick={{ fill: '#64748b' }}
                      axisLine={{ stroke: '#e2e8f0' }}
                      tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                    />
                    <YAxis
                      dataKey="name"
                      type="category"
                      className="text-xs"
                      tick={{ fill: '#64748b' }}
                      axisLine={{ stroke: '#e2e8f0' }}
                      width={75}
                    />
                    <Tooltip
                      formatter={(value: any) => `$${value.toLocaleString()}`}
                    />
                    <Bar dataKey="revenue" radius={[0, 4, 4, 0]}>
                      {data.by_product.slice(0, 10).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-slate-50">
                  <p className="text-sm text-muted-foreground">Top Product</p>
                  <p className="font-semibold">{data.by_product[0]?.name}</p>
                  <p className="text-sm text-slate-600">
                    ${data.by_product[0]?.revenue.toLocaleString()} ({data.by_product[0]?.percentage.toFixed(1)}%)
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-slate-50">
                  <p className="text-sm text-muted-foreground">Product Mix</p>
                  <p className="font-semibold">
                    {data.by_product.length} Products
                  </p>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </motion.div>
  );
}