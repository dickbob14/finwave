import React, { useState } from 'react';
import useSWR from 'swr';
import { AlertCircle, AlertTriangle, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { fetcher } from '@/lib/utils';

interface Alert {
  id: string;
  metric_id: string;
  severity: 'info' | 'warning' | 'critical';
  status: string;
  message: string;
  current_value?: number;
  threshold_value?: number;
  comparison_value?: number;
  triggered_at: string;
  notes?: string;
}

interface InsightData {
  insight: string;
  context: any;
  generated_at: string;
}

interface VarianceBadgeProps {
  workspaceId: string;
  metricId: string;
  className?: string;
}

export function VarianceBadge({ workspaceId, metricId, className }: VarianceBadgeProps) {
  const [showModal, setShowModal] = useState(false);
  
  // Poll alerts every 30 seconds
  const { data: alertsData } = useSWR(
    `/api/${workspaceId}/alerts?metric_id=${metricId}&status=active&limit=1`,
    fetcher,
    { refreshInterval: 30000 }
  );
  
  // Fetch insight when modal opens
  const { data: insightData } = useSWR(
    showModal ? `/api/${workspaceId}/insights/latest?template=variance_analysis&metric_id=${metricId}` : null,
    fetcher
  );
  
  const activeAlert = alertsData?.[0] as Alert | undefined;
  
  if (!activeAlert) {
    return null;
  }
  
  const handleAcknowledge = async () => {
    try {
      await fetch(`/api/${workspaceId}/alerts/${activeAlert.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'acknowledged' })
      });
      setShowModal(false);
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };
  
  const getAlertIcon = () => {
    if (activeAlert.severity === 'critical') {
      return (
        <AlertCircle 
          className="h-5 w-5 text-coral animate-pulse cursor-pointer" 
          onClick={() => setShowModal(true)}
        />
      );
    }
    return (
      <AlertTriangle className="h-4 w-4 text-warning" />
    );
  };
  
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-coral/10 text-coral border-coral/20';
      case 'warning': return 'bg-warning/10 text-warning border-warning/20';
      default: return 'bg-indigo/10 text-indigo border-indigo/20';
    }
  };
  
  const formatValue = (value?: number) => {
    if (value === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  return (
    <>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className={className}>
              {getAlertIcon()}
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <p className="text-sm">{activeAlert.message}</p>
            <p className="text-xs text-muted-foreground mt-1">
              {formatDate(activeAlert.triggered_at)}
            </p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
      
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-coral" />
              Variance Alert
            </DialogTitle>
            <DialogDescription>
              {metricId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Badge className={getSeverityColor(activeAlert.severity)}>
                {activeAlert.severity.toUpperCase()}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {formatDate(activeAlert.triggered_at)}
              </span>
            </div>
            
            <div className="p-4 bg-muted/50 rounded-lg">
              <p className="font-medium">{activeAlert.message}</p>
            </div>
            
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Current Value</p>
                <p className="font-medium">{formatValue(activeAlert.current_value)}</p>
              </div>
              {activeAlert.comparison_value !== undefined && (
                <div>
                  <p className="text-muted-foreground">Expected</p>
                  <p className="font-medium">{formatValue(activeAlert.comparison_value)}</p>
                </div>
              )}
              {activeAlert.threshold_value !== undefined && (
                <div>
                  <p className="text-muted-foreground">Threshold</p>
                  <p className="font-medium">{formatValue(activeAlert.threshold_value)}</p>
                </div>
              )}
            </div>
            
            {insightData && (
              <>
                <Separator />
                <div className="space-y-2">
                  <h4 className="font-medium flex items-center gap-2">
                    <span className="text-sm">AI Analysis</span>
                    <Badge variant="secondary" className="text-xs">
                      GPT-4
                    </Badge>
                  </h4>
                  <div className="p-4 bg-indigo/5 dark:bg-indigo/10 rounded-lg border border-indigo/10">
                    <p className="text-sm whitespace-pre-wrap text-navy">
                      {(insightData as InsightData).insight}
                    </p>
                  </div>
                </div>
              </>
            )}
            
            {activeAlert.notes && (
              <div className="p-3 bg-muted/30 rounded text-sm">
                <p className="text-muted-foreground mb-1">Notes</p>
                <p>{activeAlert.notes}</p>
              </div>
            )}
          </div>
          
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setShowModal(false)}>
              Close
            </Button>
            <Button onClick={handleAcknowledge}>
              Acknowledge
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}