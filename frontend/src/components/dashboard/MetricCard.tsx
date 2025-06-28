/**
 * MetricCard Component
 * Beautiful KPI cards with animations and interactive features
 */

import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus, Info, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { KPIMetric } from '@/types/dashboard';
import { Sparklines, SparklinesLine, SparklinesReferenceLine } from 'react-sparklines';
import { useState } from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface MetricCardProps {
  title: string;
  metric: KPIMetric;
  icon?: React.ReactNode;
  format?: 'currency' | 'percentage' | 'number';
  invertColors?: boolean;
  onClick?: () => void;
  loading?: boolean;
}

export function MetricCard({
  title,
  metric,
  icon,
  format = 'currency',
  invertColors = false,
  onClick,
  loading = false,
}: MetricCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  if (loading) {
    return (
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 p-6 shadow-sm animate-pulse">
        <div className="h-4 bg-slate-200 rounded w-1/2 mb-4"></div>
        <div className="h-8 bg-slate-200 rounded w-3/4 mb-2"></div>
        <div className="h-3 bg-slate-200 rounded w-1/3"></div>
      </div>
    );
  }

  const getTrendIcon = () => {
    switch (metric.trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4" />;
      case 'down':
        return <TrendingDown className="w-4 h-4" />;
      default:
        return <Minus className="w-4 h-4" />;
    }
  };

  const getTrendColor = () => {
    const isPositive = metric.trend === 'up';
    const isGood = invertColors ? !isPositive : isPositive;
    
    if (metric.status === 'critical') return 'text-red-600';
    if (metric.status === 'warning') return 'text-orange-600';
    
    return isGood ? 'text-green-600' : 'text-red-600';
  };

  const getStatusGradient = () => {
    switch (metric.status) {
      case 'critical':
        return 'from-red-50 to-red-100 border-red-200';
      case 'warning':
        return 'from-orange-50 to-orange-100 border-orange-200';
      default:
        return 'from-white to-slate-50 border-slate-200';
    }
  };

  const getSparklineColor = () => {
    switch (metric.status) {
      case 'critical':
        return '#ef4444';
      case 'warning':
        return '#f97316';
      default:
        return '#2db3a6';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.3 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      onClick={onClick}
      className={cn(
        "relative overflow-hidden rounded-xl p-6 shadow-sm transition-all duration-300 cursor-pointer",
        "bg-gradient-to-br border",
        getStatusGradient(),
        isHovered && "shadow-lg"
      )}
    >
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, currentColor 1px, transparent 1px)`,
          backgroundSize: '20px 20px'
        }} />
      </div>

      {/* Content */}
      <div className="relative">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            {icon && (
              <div className="p-2 bg-white/50 rounded-lg">
                {icon}
              </div>
            )}
            <h3 className="text-sm font-medium text-slate-600">{title}</h3>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="w-4 h-4 text-slate-400 hover:text-slate-600 transition-colors" />
              </TooltipTrigger>
              <TooltipContent>
                <p>Click for detailed analysis</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        <div className="space-y-2">
          <motion.div
            key={metric.formatted_value}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-2xl font-bold text-slate-900"
          >
            {metric.formatted_value}
          </motion.div>

          <div className="flex items-center justify-between">
            <div className={cn("flex items-center gap-1 text-sm font-medium", getTrendColor())}>
              {getTrendIcon()}
              <span>{Math.abs(metric.change_percent).toFixed(1)}%</span>
              {metric.change_value !== 0 && (
                <span className="text-slate-500">
                  ({metric.change_value > 0 ? '+' : ''}{metric.change_value.toLocaleString()})
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Sparkline */}
        {metric.sparkline && metric.sparkline.length > 0 && (
          <div className="mt-4 h-10">
            <Sparklines data={metric.sparkline} height={40} width={200}>
              <SparklinesLine
                color={getSparklineColor()}
                style={{ strokeWidth: 2 }}
              />
              <SparklinesReferenceLine type="mean" style={{ stroke: '#94a3b8', strokeOpacity: 0.5, strokeDasharray: '2,2' }} />
            </Sparklines>
          </div>
        )}

        {/* Hover Effect */}
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full"
          animate={{ translateX: isHovered ? '100%' : '-100%' }}
          transition={{ duration: 0.6, ease: 'easeInOut' }}
        />
      </div>

      {/* Status Indicator */}
      {metric.status !== 'good' && (
        <div className={cn(
          "absolute top-2 right-2 w-2 h-2 rounded-full",
          metric.status === 'critical' ? "bg-red-500" : "bg-orange-500"
        )}>
          <div className={cn(
            "absolute inset-0 rounded-full animate-ping",
            metric.status === 'critical' ? "bg-red-500" : "bg-orange-500"
          )} />
        </div>
      )}
    </motion.div>
  );
}