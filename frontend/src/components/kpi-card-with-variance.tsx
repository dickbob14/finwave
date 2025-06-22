import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { VarianceBadge } from '@/components/variance-badge';
import { cn } from '@/lib/utils';

interface KPICardProps {
  title: string;
  value: string | number;
  previousValue?: string | number;
  metricId: string;
  workspaceId: string;
  format?: 'currency' | 'percentage' | 'number';
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  className?: string;
}

export function KPICardWithVariance({
  title,
  value,
  previousValue,
  metricId,
  workspaceId,
  format = 'number',
  trend,
  trendValue,
  className
}: KPICardProps) {
  const formatValue = (val: string | number) => {
    if (typeof val === 'string') return val;
    
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(val);
      case 'percentage':
        return `${val}%`;
      default:
        return new Intl.NumberFormat('en-US').format(val);
    }
  };
  
  const getTrendIcon = () => {
    if (!trend || trend === 'neutral') return null;
    
    const Icon = trend === 'up' ? TrendingUp : TrendingDown;
    const color = trend === 'up' ? 'text-green-600' : 'text-red-600';
    
    return <Icon className={cn('h-4 w-4', color)} />;
  };
  
  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          {title}
        </CardTitle>
        <VarianceBadge 
          workspaceId={workspaceId}
          metricId={metricId}
          className="ml-2"
        />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{formatValue(value)}</div>
        {(trendValue || previousValue) && (
          <div className="flex items-center gap-1 mt-1">
            {getTrendIcon()}
            <p className="text-xs text-muted-foreground">
              {trendValue || `from ${formatValue(previousValue!)}`}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}