/**
 * CashFlowChart Component
 * Interactive cash flow visualization with forecasting
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
  ReferenceLine,
  ComposedChart,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Info, TrendingDown, TrendingUp, AlertTriangle } from 'lucide-react';
import type { CashFlowData } from '@/types/dashboard';
import { useState } from 'react';
import { cn } from '@/lib/utils';

interface CashFlowChartProps {
  data: CashFlowData;
  loading?: boolean;
}

export function CashFlowChart({ data, loading = false }: CashFlowChartProps) {
  const [showForecast, setShowForecast] = useState(true);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

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

  // Prepare chart data
  const chartData = data.periods.map((period, index) => ({
    period,
    cashIn: data.cash_in[index],
    cashOut: -Math.abs(data.cash_out[index]),
    netCashFlow: data.net_cash_flow[index],
    cumulativeCash: data.cumulative_cash[index],
    ...(data.forecast && index >= data.periods.length - data.forecast.periods.length
      ? {
          projectedFlow: data.forecast.projected_cash_flow[index - (data.periods.length - data.forecast.periods.length)],
          projectedBalance: data.forecast.projected_balance[index - (data.periods.length - data.forecast.periods.length)],
          confidenceLower: data.forecast.confidence_interval.lower[index - (data.periods.length - data.forecast.periods.length)],
          confidenceUpper: data.forecast.confidence_interval.upper[index - (data.periods.length - data.forecast.periods.length)],
        }
      : {}),
  }));

  const currentCash = data.cumulative_cash[data.cumulative_cash.length - 1];
  const avgBurnRate = data.cash_out.reduce((a, b) => a + b, 0) / data.cash_out.length;
  const runway = currentCash > 0 && avgBurnRate > 0 ? Math.floor(currentCash / avgBurnRate) : 0;

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
                ${Math.abs(entry.value).toLocaleString()}
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
              <CardTitle className="text-lg font-semibold">Cash Flow Analysis</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Monthly cash movements and projections
              </p>
            </div>
            <div className="flex items-center gap-2">
              {runway > 0 && runway < 6 && (
                <Badge variant="destructive" className="gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  {runway} months runway
                </Badge>
              )}
              <Badge
                variant={showForecast ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => setShowForecast(!showForecast)}
              >
                Forecast {showForecast ? 'ON' : 'OFF'}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={chartData}
                margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                onMouseMove={(state: any) => {
                  if (state.activeTooltipIndex !== undefined) {
                    setActiveIndex(state.activeTooltipIndex);
                  }
                }}
                onMouseLeave={() => setActiveIndex(null)}
              >
                <defs>
                  <linearGradient id="cashInGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2db3a6" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#2db3a6" stopOpacity={0.1} />
                  </linearGradient>
                  <linearGradient id="cashOutGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1} />
                  </linearGradient>
                  <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
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
                  className="text-xs"
                  tick={{ fill: '#64748b' }}
                  axisLine={{ stroke: '#e2e8f0' }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  verticalAlign="top"
                  height={36}
                  iconType="circle"
                  wrapperStyle={{ fontSize: '12px' }}
                />
                <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="3 3" />
                
                {/* Cash In/Out Bars */}
                <Bar
                  dataKey="cashIn"
                  name="Cash In"
                  fill="#2db3a6"
                  opacity={0.8}
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  dataKey="cashOut"
                  name="Cash Out"
                  fill="#ef4444"
                  opacity={0.8}
                  radius={[0, 0, 4, 4]}
                />
                
                {/* Cumulative Cash Line */}
                <Line
                  type="monotone"
                  dataKey="cumulativeCash"
                  name="Cash Balance"
                  stroke="#5b5bf2"
                  strokeWidth={3}
                  dot={{ fill: '#5b5bf2', r: 4 }}
                  activeDot={{ r: 6 }}
                />
                
                {/* Forecast */}
                {showForecast && data.forecast && (
                  <>
                    <Area
                      type="monotone"
                      dataKey="confidenceUpper"
                      stackId="1"
                      stroke="none"
                      fill="#5b5bf2"
                      fillOpacity={0.1}
                    />
                    <Area
                      type="monotone"
                      dataKey="confidenceLower"
                      stackId="1"
                      stroke="none"
                      fill="#ffffff"
                      fillOpacity={1}
                    />
                    <Line
                      type="monotone"
                      dataKey="projectedBalance"
                      name="Projected Balance"
                      stroke="#5b5bf2"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={false}
                    />
                  </>
                )}
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t">
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="text-center p-3 rounded-lg bg-slate-50"
            >
              <p className="text-sm text-muted-foreground">Current Balance</p>
              <p className={cn(
                "text-xl font-bold mt-1",
                currentCash >= 0 ? "text-green-600" : "text-red-600"
              )}>
                ${currentCash.toLocaleString()}
              </p>
            </motion.div>
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="text-center p-3 rounded-lg bg-slate-50"
            >
              <p className="text-sm text-muted-foreground">Avg Burn Rate</p>
              <p className="text-xl font-bold mt-1 text-orange-600">
                ${avgBurnRate.toLocaleString()}/mo
              </p>
            </motion.div>
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="text-center p-3 rounded-lg bg-slate-50"
            >
              <p className="text-sm text-muted-foreground">Cash Runway</p>
              <p className={cn(
                "text-xl font-bold mt-1",
                runway > 12 ? "text-green-600" : runway > 6 ? "text-orange-600" : "text-red-600"
              )}>
                {runway} months
              </p>
            </motion.div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}