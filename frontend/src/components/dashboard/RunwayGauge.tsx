/**
 * RunwayGauge Component
 * Visual cash runway indicator with gauge chart
 */

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, TrendingDown, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RunwayGaugeProps {
  runwayMonths: number;
  burnRate: number;
  cashBalance: number;
  loading?: boolean;
}

export function RunwayGauge({ runwayMonths, burnRate, cashBalance, loading = false }: RunwayGaugeProps) {
  if (loading) {
    return (
      <Card className="animate-pulse">
        <CardHeader>
          <div className="h-6 bg-slate-200 rounded w-1/2"></div>
        </CardHeader>
        <CardContent>
          <div className="h-48 bg-slate-100 rounded"></div>
        </CardContent>
      </Card>
    );
  }

  // Determine health status
  const getStatus = () => {
    if (runwayMonths > 18) return { color: 'green', label: 'Healthy', icon: Zap };
    if (runwayMonths > 12) return { color: 'blue', label: 'Good', icon: TrendingDown };
    if (runwayMonths > 6) return { color: 'orange', label: 'Warning', icon: AlertTriangle };
    return { color: 'red', label: 'Critical', icon: AlertTriangle };
  };

  const status = getStatus();
  const StatusIcon = status.icon;

  // Calculate gauge angle (0-180 degrees)
  const maxMonths = 24;
  const angle = Math.min((runwayMonths / maxMonths) * 180, 180);

  // Generate gauge segments
  const segments = [
    { start: 0, end: 45, color: 'bg-red-500', label: '0-6' },
    { start: 45, end: 90, color: 'bg-orange-500', label: '6-12' },
    { start: 90, end: 135, color: 'bg-blue-500', label: '12-18' },
    { start: 135, end: 180, color: 'bg-green-500', label: '18+' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="overflow-hidden">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold">Cash Runway</CardTitle>
            <Badge
              variant={status.color === 'green' ? 'default' : status.color === 'red' ? 'destructive' : 'secondary'}
              className="gap-1"
            >
              <StatusIcon className="w-3 h-3" />
              {status.label}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {/* Gauge Chart */}
          <div className="relative h-32 mb-4">
            <svg viewBox="0 0 200 100" className="w-full h-full">
              {/* Background segments */}
              {segments.map((segment, index) => (
                <path
                  key={index}
                  d={`M ${100 - 80 * Math.cos((segment.start * Math.PI) / 180)} ${100 - 80 * Math.sin((segment.start * Math.PI) / 180)}
                     A 80 80 0 0 1 ${100 - 80 * Math.cos((segment.end * Math.PI) / 180)} ${100 - 80 * Math.sin((segment.end * Math.PI) / 180)}
                     L ${100 - 60 * Math.cos((segment.end * Math.PI) / 180)} ${100 - 60 * Math.sin((segment.end * Math.PI) / 180)}
                     A 60 60 0 0 0 ${100 - 60 * Math.cos((segment.start * Math.PI) / 180)} ${100 - 60 * Math.sin((segment.start * Math.PI) / 180)} Z`}
                  className={cn(segment.color, 'opacity-20')}
                />
              ))}

              {/* Active segment */}
              <motion.path
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1.5, ease: 'easeOut' }}
                d={`M 20 100 A 80 80 0 ${angle > 90 ? 1 : 0} 1 ${100 - 80 * Math.cos((angle * Math.PI) / 180)} ${100 - 80 * Math.sin((angle * Math.PI) / 180)}`}
                fill="none"
                stroke={
                  runwayMonths > 18 ? '#10b981' :
                  runwayMonths > 12 ? '#3b82f6' :
                  runwayMonths > 6 ? '#f97316' : '#ef4444'
                }
                strokeWidth="20"
                strokeLinecap="round"
              />

              {/* Needle */}
              <motion.line
                initial={{ rotate: 0 }}
                animate={{ rotate: angle }}
                transition={{ duration: 1.5, ease: 'easeOut' }}
                x1="100"
                y1="100"
                x2="100"
                y2="30"
                stroke="#1a2841"
                strokeWidth="3"
                strokeLinecap="round"
                style={{ transformOrigin: '100px 100px' }}
              />

              {/* Center circle */}
              <circle cx="100" cy="100" r="10" fill="#1a2841" />

              {/* Labels */}
              <text x="20" y="95" className="text-xs fill-slate-500">0</text>
              <text x="100" y="20" className="text-xs fill-slate-500" textAnchor="middle">12</text>
              <text x="180" y="95" className="text-xs fill-slate-500" textAnchor="end">24+</text>
            </svg>

            {/* Center value */}
            <div className="absolute inset-0 flex items-center justify-center mt-8">
              <div className="text-center">
                <motion.div
                  key={runwayMonths}
                  initial={{ scale: 1.2, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="text-3xl font-bold"
                >
                  {runwayMonths}
                </motion.div>
                <div className="text-sm text-muted-foreground">months</div>
              </div>
            </div>
          </div>

          {/* Metrics */}
          <div className="space-y-3 pt-4 border-t">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Monthly Burn Rate</span>
              <span className="text-sm font-medium text-red-600">
                ${Math.abs(burnRate).toLocaleString()}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Cash Balance</span>
              <span className="text-sm font-medium">
                ${cashBalance.toLocaleString()}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Months Until Depletion</span>
              <span className={cn(
                "text-sm font-medium",
                runwayMonths > 12 ? "text-green-600" : runwayMonths > 6 ? "text-orange-600" : "text-red-600"
              )}>
                {runwayMonths} months
              </span>
            </div>
          </div>

          {/* Warning message */}
          {runwayMonths <= 6 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg"
            >
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5" />
                <div className="text-sm text-red-800">
                  <p className="font-semibold">Action Required</p>
                  <p className="mt-1">
                    Your cash runway is critically low. Consider reducing expenses or securing additional funding.
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}