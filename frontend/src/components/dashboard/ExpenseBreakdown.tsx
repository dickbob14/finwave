/**
 * ExpenseBreakdown Component
 * Expense analysis with pie/donut charts
 */

import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { ExpenseAnalysis } from '@/types/dashboard';
import { cn } from '@/lib/utils';

interface ExpenseBreakdownProps {
  data: ExpenseAnalysis;
  loading?: boolean;
}

const COLORS = ['#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e', '#14b8a6', '#06b6d4'];

export function ExpenseBreakdown({ data, loading = false }: ExpenseBreakdownProps) {
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

  const totalExpenses = data.by_category.reduce((sum, cat) => sum + cat.amount, 0);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-slate-200">
          <p className="font-semibold text-sm">{data.name}</p>
          <p className="text-sm mt-1">
            ${data.value.toLocaleString()} ({data.payload.percentage.toFixed(1)}%)
          </p>
        </div>
      );
    }
    return null;
  };

  const renderCustomLabel = (entry: any) => {
    if (entry.percentage < 5) return null;
    return `${entry.percentage.toFixed(0)}%`;
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
              <CardTitle className="text-lg font-semibold">Expense Analysis</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Breakdown by category and vendor
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-muted-foreground">Total Expenses</p>
              <p className="text-lg font-semibold text-red-600">
                ${totalExpenses.toLocaleString()}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="category" className="space-y-4">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="category">By Category</TabsTrigger>
              <TabsTrigger value="vendor">By Vendor</TabsTrigger>
            </TabsList>

            <TabsContent value="category" className="space-y-4">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data.by_category}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={renderCustomLabel}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="amount"
                    >
                      {data.by_category.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend
                      verticalAlign="bottom"
                      height={36}
                      formatter={(value: string, entry: any) => (
                        <span className="text-xs">
                          {value} ({entry.payload.percentage.toFixed(1)}%)
                        </span>
                      )}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Category List */}
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {data.by_category.map((category, index) => (
                  <motion.div
                    key={category.category}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                      />
                      <span className="text-sm font-medium">{category.category}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium">
                        ${category.amount.toLocaleString()}
                      </span>
                      <div className={cn(
                        "flex items-center gap-1 text-xs",
                        category.trend === 'up' ? "text-red-600" : 
                        category.trend === 'down' ? "text-green-600" : 
                        "text-slate-500"
                      )}>
                        {category.trend === 'up' && <TrendingUp className="w-3 h-3" />}
                        {category.trend === 'down' && <TrendingDown className="w-3 h-3" />}
                        {category.trend === 'stable' && <Minus className="w-3 h-3" />}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="vendor" className="space-y-4">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data.by_vendor.slice(0, 10)}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      fill="#8884d8"
                      paddingAngle={5}
                      dataKey="amount"
                    >
                      {data.by_vendor.slice(0, 10).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Vendor List */}
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {data.by_vendor.slice(0, 10).map((vendor, index) => (
                  <motion.div
                    key={vendor.name}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                      />
                      <span className="text-sm font-medium truncate max-w-[150px]">
                        {vendor.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">
                        ${vendor.amount.toLocaleString()}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        ({vendor.percentage.toFixed(1)}%)
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </motion.div>
  );
}