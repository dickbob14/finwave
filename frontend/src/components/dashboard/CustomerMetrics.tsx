/**
 * CustomerMetrics Component
 * Customer acquisition, retention, and value metrics
 */

import { motion } from 'framer-motion';
import {
  Line,
  LineChart,
  Bar,
  BarChart,
  Area,
  AreaChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Users, UserPlus, UserMinus, DollarSign } from 'lucide-react';
import { useCustomerMetrics } from '@/hooks/useDashboard';
import { cn } from '@/lib/utils';

interface CustomerMetricsProps {
  companyId: string;
}

export function CustomerMetrics({ companyId }: CustomerMetricsProps) {
  const { customers, isLoading } = useCustomerMetrics(companyId);

  if (isLoading || !customers) {
    return (
      <Card className="animate-pulse">
        <CardHeader>
          <div className="h-6 bg-slate-200 rounded w-1/2"></div>
        </CardHeader>
        <CardContent>
          <div className="h-64 bg-slate-100 rounded"></div>
        </CardContent>
      </Card>
    );
  }

  // Prepare chart data
  const acquisitionData = customers.acquisition.periods.map((period, index) => ({
    period,
    newCustomers: customers.acquisition.new_customers[index],
    cac: customers.acquisition.cac_trend[index],
  }));

  const retentionData = customers.retention.cohorts.map(cohort => ({
    cohort: cohort.month,
    ...cohort.retention_curve.reduce((acc, value, index) => ({
      ...acc,
      [`month${index}`]: value,
    }), {}),
  }));

  const avgRetention = customers.retention.cohorts[0]?.retention_curve[11] || 0;
  const totalCustomers = customers.acquisition.new_customers.reduce((a, b) => a + b, 0);
  const avgCAC = customers.acquisition.cac_trend.reduce((a, b) => a + b, 0) / customers.acquisition.cac_trend.length;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-slate-200">
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
                {entry.name === 'CAC' ? `$${entry.value}` : entry.value}
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
      className="space-y-6"
    >
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg font-semibold">Customer Metrics</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Acquisition, retention, and revenue analysis
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{totalCustomers}</p>
                <p className="text-xs text-muted-foreground">Total Customers</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold">${customers.retention.average_ltv.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">Avg LTV</p>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Customer Acquisition */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-sm">Customer Acquisition</h3>
              <Badge variant="outline" className="text-xs">
                Avg CAC: ${avgCAC.toFixed(0)}
              </Badge>
            </div>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={acquisitionData}
                  margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
                >
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
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    className="text-xs"
                    tick={{ fill: '#64748b' }}
                    axisLine={{ stroke: '#e2e8f0' }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    verticalAlign="top"
                    height={36}
                    iconType="circle"
                    wrapperStyle={{ fontSize: '12px' }}
                  />
                  <Bar
                    yAxisId="left"
                    dataKey="newCustomers"
                    name="New Customers"
                    fill="#2db3a6"
                    opacity={0.8}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="cac"
                    name="CAC"
                    stroke="#f97316"
                    strokeWidth={2}
                    dot={{ fill: '#f97316', r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Retention Cohorts */}
          <div className="space-y-4 mt-8">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-sm">Retention Cohorts</h3>
              <Badge
                variant={avgRetention > 80 ? 'default' : avgRetention > 60 ? 'secondary' : 'destructive'}
                className="text-xs"
              >
                12M Retention: {avgRetention.toFixed(0)}%
              </Badge>
            </div>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={retentionData.slice(0, 6)}
                  margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
                >
                  <defs>
                    <linearGradient id="retentionGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#5b5bf2" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#5b5bf2" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                  <XAxis
                    dataKey="cohort"
                    className="text-xs"
                    tick={{ fill: '#64748b' }}
                    axisLine={{ stroke: '#e2e8f0' }}
                  />
                  <YAxis
                    className="text-xs"
                    tick={{ fill: '#64748b' }}
                    axisLine={{ stroke: '#e2e8f0' }}
                    domain={[0, 100]}
                  />
                  <Tooltip
                    formatter={(value: any) => `${value}%`}
                  />
                  {[0, 3, 6, 9, 11].map((monthIndex) => (
                    <Area
                      key={monthIndex}
                      type="monotone"
                      dataKey={`month${monthIndex}`}
                      stackId="1"
                      stroke="#5b5bf2"
                      fill="url(#retentionGradient)"
                      name={`Month ${monthIndex + 1}`}
                    />
                  ))}
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Revenue Distribution */}
          <div className="space-y-4 mt-8">
            <h3 className="font-semibold text-sm">Revenue Distribution</h3>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {customers.revenue_distribution.buckets.map((bucket, index) => (
                <motion.div
                  key={bucket.range}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-3 rounded-lg bg-slate-50 border border-slate-200"
                >
                  <p className="text-xs text-muted-foreground">{bucket.range}</p>
                  <p className="text-lg font-semibold">{bucket.count}</p>
                  <p className="text-xs text-slate-600">
                    ${(bucket.revenue / 1000).toFixed(0)}k revenue
                  </p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Churn Analysis */}
          <div className="grid grid-cols-3 gap-4 mt-8 pt-4 border-t">
            <div className="text-center p-3 rounded-lg bg-slate-50">
              <UserPlus className="w-5 h-5 text-green-600 mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">Avg New/Month</p>
              <p className="text-lg font-semibold">
                {Math.round(customers.acquisition.new_customers.reduce((a, b) => a + b, 0) / customers.acquisition.new_customers.length)}
              </p>
            </div>
            <div className="text-center p-3 rounded-lg bg-slate-50">
              <UserMinus className="w-5 h-5 text-red-600 mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">Avg Churn/Month</p>
              <p className="text-lg font-semibold">
                {Math.round(customers.retention.churn_by_month.reduce((a, b) => a + b, 0) / customers.retention.churn_by_month.length)}
              </p>
            </div>
            <div className="text-center p-3 rounded-lg bg-slate-50">
              <DollarSign className="w-5 h-5 text-purple-600 mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">Revenue/Customer</p>
              <p className="text-lg font-semibold">
                ${Math.round(customers.retention.average_ltv / 12)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}