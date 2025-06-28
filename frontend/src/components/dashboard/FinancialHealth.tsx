/**
 * FinancialHealth Component
 * Display financial health indicators
 */

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Activity, Shield, TrendingUp, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { DashboardSummary } from '@/types/dashboard';

interface FinancialHealthProps {
  dashboard: DashboardSummary;
  loading?: boolean;
}

interface HealthMetric {
  label: string;
  value: number;
  target: number;
  unit: string;
  status: 'good' | 'warning' | 'critical';
  description: string;
}

export function FinancialHealth({ dashboard, loading = false }: FinancialHealthProps) {
  if (loading) {
    return (
      <Card className="animate-pulse">
        <CardHeader>
          <div className="h-6 bg-slate-200 rounded w-1/2"></div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="space-y-2">
                <div className="h-4 bg-slate-200 rounded w-1/3"></div>
                <div className="h-8 bg-slate-100 rounded"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const healthMetrics: HealthMetric[] = [
    {
      label: 'Current Ratio',
      value: dashboard.kpis.current_ratio.value,
      target: 1.5,
      unit: 'ratio',
      status: dashboard.kpis.current_ratio.status,
      description: 'Ability to pay short-term obligations',
    },
    {
      label: 'Quick Ratio',
      value: dashboard.kpis.quick_ratio.value,
      target: 1.0,
      unit: 'ratio',
      status: dashboard.kpis.quick_ratio.status,
      description: 'Immediate liquidity position',
    },
    {
      label: 'Gross Margin',
      value: dashboard.kpis.gross_margin.value,
      target: 70,
      unit: '%',
      status: dashboard.kpis.gross_margin.status,
      description: 'Profitability after direct costs',
    },
    {
      label: 'Debt to Equity',
      value: dashboard.kpis.debt_to_equity.value,
      target: 0.5,
      unit: 'ratio',
      status: dashboard.kpis.debt_to_equity.status,
      description: 'Financial leverage',
    },
  ];

  const getProgressColor = (status: string) => {
    switch (status) {
      case 'good':
        return 'bg-green-500';
      case 'warning':
        return 'bg-orange-500';
      case 'critical':
        return 'bg-red-500';
      default:
        return 'bg-slate-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'good':
        return <Shield className="w-4 h-4 text-green-600" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-orange-600" />;
      case 'critical':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Activity className="w-4 h-4 text-slate-600" />;
    }
  };

  const overallHealth = healthMetrics.filter(m => m.status === 'good').length / healthMetrics.length;
  const healthScore = Math.round(overallHealth * 100);

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
              <CardTitle className="text-lg font-semibold">Financial Health</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Key liquidity and leverage metrics
              </p>
            </div>
            <div className="text-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200 }}
                className={cn(
                  "w-16 h-16 rounded-full flex items-center justify-center font-bold text-white",
                  healthScore >= 75 ? "bg-green-500" :
                  healthScore >= 50 ? "bg-orange-500" :
                  "bg-red-500"
                )}
              >
                {healthScore}%
              </motion.div>
              <p className="text-xs text-muted-foreground mt-1">Health Score</p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {healthMetrics.map((metric, index) => (
            <motion.div
              key={metric.label}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="space-y-2"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(metric.status)}
                  <div>
                    <p className="text-sm font-medium">{metric.label}</p>
                    <p className="text-xs text-muted-foreground">{metric.description}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold">
                    {metric.value.toFixed(2)}{metric.unit === '%' ? '%' : ''}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Target: {metric.target}{metric.unit === '%' ? '%' : ''}
                  </p>
                </div>
              </div>
              <div className="relative">
                <Progress
                  value={Math.min((metric.value / metric.target) * 100, 100)}
                  className="h-2"
                />
                <div
                  className={cn(
                    "absolute inset-0 h-2 rounded-full opacity-30",
                    getProgressColor(metric.status)
                  )}
                  style={{
                    width: `${Math.min((metric.value / metric.target) * 100, 100)}%`,
                  }}
                />
              </div>
            </motion.div>
          ))}

          {/* Working Capital */}
          <div className="pt-4 border-t">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Working Capital</p>
                <p className="text-xs text-muted-foreground">
                  Available for operations
                </p>
              </div>
              <div className="text-right">
                <p className={cn(
                  "text-lg font-semibold",
                  dashboard.kpis.working_capital.value >= 0 ? "text-green-600" : "text-red-600"
                )}>
                  ${dashboard.kpis.working_capital.formatted_value}
                </p>
                <Badge
                  variant={dashboard.kpis.working_capital.status === 'good' ? 'default' : 'destructive'}
                  className="text-xs"
                >
                  {dashboard.kpis.working_capital.trend === 'up' ? '+' : ''}{dashboard.kpis.working_capital.change_percent.toFixed(1)}%
                </Badge>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          {healthScore < 75 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded-lg"
            >
              <div className="flex items-start gap-2">
                <TrendingUp className="w-4 h-4 text-orange-600 mt-0.5" />
                <div className="text-sm text-orange-800">
                  <p className="font-semibold">Improvement Areas</p>
                  <ul className="mt-1 space-y-1 list-disc list-inside">
                    {healthMetrics
                      .filter(m => m.status !== 'good')
                      .map(m => (
                        <li key={m.label} className="text-xs">
                          Improve {m.label} (current: {m.value.toFixed(2)}, target: {m.target})
                        </li>
                      ))}
                  </ul>
                </div>
              </div>
            </motion.div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}