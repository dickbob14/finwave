import React, { useState } from 'react';
import useSWR, { mutate } from 'swr';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, CheckCircle, Clock, Filter, RefreshCw } from 'lucide-react';
import { fetcher } from '@/lib/utils';

interface Alert {
  id: string;
  metric_id: string;
  rule_name: string;
  severity: 'info' | 'warning' | 'critical';
  status: 'active' | 'acknowledged' | 'resolved';
  message: string;
  current_value?: number;
  threshold_value?: number;
  comparison_value?: number;
  triggered_at: string;
  acknowledged_at?: string;
  acknowledged_by?: string;
  notes?: string;
}

interface VarianceAlertsProps {
  workspaceId: string;
}

export function VarianceAlerts({ workspaceId }: VarianceAlertsProps) {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [notes, setNotes] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  
  // Build query params
  const queryParams = new URLSearchParams();
  if (statusFilter !== 'all') queryParams.append('status', statusFilter);
  if (severityFilter !== 'all') queryParams.append('severity', severityFilter);
  queryParams.append('days', '30');
  queryParams.append('limit', '100');
  
  const { data: alerts, error, isLoading } = useSWR(
    `/api/${workspaceId}/alerts?${queryParams.toString()}`,
    fetcher,
    { refreshInterval: 30000 }
  );
  
  const handleCheckNow = async () => {
    try {
      await fetch(`/api/${workspaceId}/alerts/check-now`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      mutate(`/api/${workspaceId}/alerts?${queryParams.toString()}`);
    } catch (error) {
      console.error('Failed to trigger check:', error);
    }
  };
  
  const handleUpdateAlert = async (status: string) => {
    if (!selectedAlert) return;
    
    setIsUpdating(true);
    try {
      await fetch(`/api/${workspaceId}/alerts/${selectedAlert.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, notes })
      });
      
      mutate(`/api/${workspaceId}/alerts?${queryParams.toString()}`);
      setSelectedAlert(null);
      setNotes('');
    } catch (error) {
      console.error('Failed to update alert:', error);
    } finally {
      setIsUpdating(false);
    }
  };
  
  const getSeverityBadge = (severity: string) => {
    const styles = {
      critical: 'bg-red-100 text-red-800 border-red-200',
      warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      info: 'bg-blue-100 text-blue-800 border-blue-200'
    };
    
    return (
      <Badge className={styles[severity as keyof typeof styles] || styles.info}>
        {severity.toUpperCase()}
      </Badge>
    );
  };
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'acknowledged':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'resolved':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      default:
        return null;
    }
  };
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  const formatValue = (value?: number) => {
    if (value === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(value);
  };
  
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Variance Alerts</CardTitle>
            <Button onClick={handleCheckNow} size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Check Now
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="flex gap-4 mb-6">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="acknowledged">Acknowledged</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severity</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="warning">Warning</SelectItem>
                <SelectItem value="info">Info</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          {/* Alerts Table */}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]">Status</TableHead>
                  <TableHead>Metric</TableHead>
                  <TableHead>Message</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Current</TableHead>
                  <TableHead>Expected</TableHead>
                  <TableHead>Triggered</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center">
                      Loading alerts...
                    </TableCell>
                  </TableRow>
                ) : alerts?.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center">
                      No alerts found
                    </TableCell>
                  </TableRow>
                ) : (
                  alerts?.map((alert: Alert) => (
                    <TableRow key={alert.id}>
                      <TableCell>{getStatusIcon(alert.status)}</TableCell>
                      <TableCell className="font-medium">
                        {alert.metric_id.replace(/_/g, ' ')}
                      </TableCell>
                      <TableCell className="max-w-[300px] truncate">
                        {alert.message}
                      </TableCell>
                      <TableCell>{getSeverityBadge(alert.severity)}</TableCell>
                      <TableCell>{formatValue(alert.current_value)}</TableCell>
                      <TableCell>{formatValue(alert.comparison_value)}</TableCell>
                      <TableCell>{formatDate(alert.triggered_at)}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedAlert(alert);
                            setNotes(alert.notes || '');
                          }}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
      
      {/* Alert Detail Dialog */}
      <Dialog open={!!selectedAlert} onOpenChange={() => setSelectedAlert(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Alert Details</DialogTitle>
            <DialogDescription>
              {selectedAlert?.metric_id.replace(/_/g, ' ')}
            </DialogDescription>
          </DialogHeader>
          
          {selectedAlert && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                {getSeverityBadge(selectedAlert.severity)}
                <span className="text-sm text-muted-foreground">
                  {formatDate(selectedAlert.triggered_at)}
                </span>
              </div>
              
              <div className="p-4 bg-muted/50 rounded-lg">
                <p>{selectedAlert.message}</p>
              </div>
              
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Current Value</p>
                  <p className="font-medium">{formatValue(selectedAlert.current_value)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Expected Value</p>
                  <p className="font-medium">{formatValue(selectedAlert.comparison_value)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Threshold</p>
                  <p className="font-medium">{formatValue(selectedAlert.threshold_value)}</p>
                </div>
              </div>
              
              {selectedAlert.acknowledged_at && (
                <div className="text-sm">
                  <p className="text-muted-foreground">
                    Acknowledged by {selectedAlert.acknowledged_by} on{' '}
                    {formatDate(selectedAlert.acknowledged_at)}
                  </p>
                </div>
              )}
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Notes</label>
                <Textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add notes about this alert..."
                  rows={3}
                />
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedAlert(null)}>
              Cancel
            </Button>
            {selectedAlert?.status === 'active' && (
              <Button
                onClick={() => handleUpdateAlert('acknowledged')}
                disabled={isUpdating}
              >
                Acknowledge
              </Button>
            )}
            {selectedAlert?.status !== 'resolved' && (
              <Button
                onClick={() => handleUpdateAlert('resolved')}
                disabled={isUpdating}
                variant="default"
              >
                Resolve
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}