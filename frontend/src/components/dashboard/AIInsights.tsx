/**
 * AIInsights Component
 * Display AI-powered insights and alerts
 */

import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Sparkles, AlertTriangle, Info, TrendingUp, X } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import type { Alert as AlertType } from '@/types/dashboard';

interface AIInsightsProps {
  insights: string[];
  alerts: AlertType[];
}

export function AIInsights({ insights, alerts }: AIInsightsProps) {
  const [dismissedInsights, setDismissedInsights] = useState<number[]>([]);
  const [dismissedAlerts, setDismissedAlerts] = useState<string[]>([]);

  const visibleInsights = insights.filter((_, index) => !dismissedInsights.includes(index));
  const visibleAlerts = alerts.filter(alert => !dismissedAlerts.includes(alert.id));

  if (visibleInsights.length === 0 && visibleAlerts.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      {/* AI Insights */}
      {visibleInsights.length > 0 && (
        <Card className="bg-gradient-to-r from-purple-50 to-indigo-50 border-purple-200">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Sparkles className="w-5 h-5 text-purple-600" />
              </div>
              <div className="flex-1 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-purple-900">AI Insights</h3>
                  <Badge variant="secondary" className="bg-purple-100 text-purple-700">
                    Powered by AI
                  </Badge>
                </div>
                <AnimatePresence>
                  {visibleInsights.map((insight, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="flex items-start justify-between gap-2"
                    >
                      <p className="text-sm text-slate-700">{insight}</p>
                      <button
                        onClick={() => setDismissedInsights([...dismissedInsights, index])}
                        className="text-slate-400 hover:text-slate-600 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Critical Alerts */}
      <AnimatePresence>
        {visibleAlerts.map((alert) => (
          <motion.div
            key={alert.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
          >
            <Alert
              className={cn(
                "border-l-4",
                alert.type === 'critical' && "border-l-red-500 bg-red-50",
                alert.type === 'warning' && "border-l-orange-500 bg-orange-50",
                alert.type === 'info' && "border-l-blue-500 bg-blue-50"
              )}
            >
              <div className="flex items-start gap-3">
                {alert.type === 'critical' && <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />}
                {alert.type === 'warning' && <TrendingUp className="w-5 h-5 text-orange-600 mt-0.5" />}
                {alert.type === 'info' && <Info className="w-5 h-5 text-blue-600 mt-0.5" />}
                <div className="flex-1">
                  <h4 className="font-semibold text-sm mb-1">{alert.title}</h4>
                  <AlertDescription className="text-sm">
                    {alert.message}
                  </AlertDescription>
                  {alert.metric && (
                    <Badge variant="outline" className="mt-2 text-xs">
                      Related to: {alert.metric}
                    </Badge>
                  )}
                </div>
                <button
                  onClick={() => setDismissedAlerts([...dismissedAlerts, alert.id])}
                  className="text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </Alert>
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.div>
  );
}