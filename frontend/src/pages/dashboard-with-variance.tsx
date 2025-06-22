import React from 'react';
import { KPICardWithVariance } from '@/components/kpi-card-with-variance';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, TrendingUp, Users, DollarSign, Activity } from 'lucide-react';
import useSWR from 'swr';
import { fetcher } from '@/lib/utils';

interface DashboardProps {
  workspaceId: string;
}

export function DashboardWithVariance({ workspaceId }: DashboardProps) {
  // Fetch alert summary
  const { data: alertSummary } = useSWR(
    `/api/${workspaceId}/alerts/summary`,
    fetcher,
    { refreshInterval: 60000 }
  );
  
  // Fetch latest metrics
  const { data: metrics } = useSWR(
    `/api/${workspaceId}/metrics/latest`,
    fetcher,
    { refreshInterval: 60000 }
  );
  
  const hasActiveAlerts = alertSummary?.active > 0;
  
  return (
    <div className="space-y-6">
      {/* Alert Summary Banner */}
      {hasActiveAlerts && (
        <Alert className="border-yellow-200 bg-yellow-50">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>{alertSummary.active} active alerts</strong> require your attention.
            {alertSummary.by_severity.critical > 0 && (
              <span className="ml-2 text-red-600">
                {alertSummary.by_severity.critical} critical
              </span>
            )}
          </AlertDescription>
        </Alert>
      )}
      
      {/* Key Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICardWithVariance
          title="Revenue"
          value={metrics?.revenue?.value || 0}
          previousValue={metrics?.revenue?.previous_value}
          metricId="revenue"
          workspaceId={workspaceId}
          format="currency"
          trend="up"
          trendValue="+12.5%"
        />
        
        <KPICardWithVariance
          title="Gross Margin"
          value={metrics?.gross_margin?.value || 0}
          metricId="gross_margin"
          workspaceId={workspaceId}
          format="percentage"
          trend="down"
          trendValue="-2.1pp"
        />
        
        <KPICardWithVariance
          title="Burn Rate"
          value={metrics?.burn_rate?.value || 0}
          metricId="burn_rate"
          workspaceId={workspaceId}
          format="currency"
          trend="up"
          trendValue="+8.3%"
        />
        
        <KPICardWithVariance
          title="Runway"
          value={`${metrics?.runway_months?.value || 0} months`}
          metricId="runway_months"
          workspaceId={workspaceId}
          trend="down"
          trendValue="from 18 months"
        />
      </div>
      
      {/* Tabbed Content */}
      <Tabs defaultValue="financial" className="space-y-4">
        <TabsList>
          <TabsTrigger value="financial">Financial</TabsTrigger>
          <TabsTrigger value="saas">SaaS Metrics</TabsTrigger>
          <TabsTrigger value="operational">Operational</TabsTrigger>
        </TabsList>
        
        <TabsContent value="financial" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <KPICardWithVariance
              title="EBITDA"
              value={metrics?.ebitda?.value || 0}
              metricId="ebitda"
              workspaceId={workspaceId}
              format="currency"
            />
            <KPICardWithVariance
              title="Operating Expenses"
              value={metrics?.opex?.value || 0}
              metricId="opex"
              workspaceId={workspaceId}
              format="currency"
            />
            <KPICardWithVariance
              title="Cash Balance"
              value={metrics?.cash?.value || 0}
              metricId="cash"
              workspaceId={workspaceId}
              format="currency"
            />
          </div>
        </TabsContent>
        
        <TabsContent value="saas" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <KPICardWithVariance
              title="MRR"
              value={metrics?.mrr?.value || 0}
              metricId="mrr"
              workspaceId={workspaceId}
              format="currency"
            />
            <KPICardWithVariance
              title="Net Retention"
              value={metrics?.net_retention_rate?.value || 0}
              metricId="net_retention_rate"
              workspaceId={workspaceId}
              format="percentage"
            />
            <KPICardWithVariance
              title="LTV:CAC Ratio"
              value={`${metrics?.ltv_to_cac_ratio?.value || 0}x`}
              metricId="ltv_to_cac_ratio"
              workspaceId={workspaceId}
            />
          </div>
        </TabsContent>
        
        <TabsContent value="operational" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <KPICardWithVariance
              title="Headcount"
              value={metrics?.total_headcount?.value || 0}
              metricId="total_headcount"
              workspaceId={workspaceId}
              format="number"
            />
            <KPICardWithVariance
              title="Revenue per FTE"
              value={metrics?.revenue_per_fte?.value || 0}
              metricId="revenue_per_fte"
              workspaceId={workspaceId}
              format="currency"
            />
            <KPICardWithVariance
              title="Payroll % of Revenue"
              value={metrics?.payroll_as_pct_revenue?.value || 0}
              metricId="payroll_as_pct_revenue"
              workspaceId={workspaceId}
              format="percentage"
            />
          </div>
        </TabsContent>
      </Tabs>
      
      {/* Alert Details Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Alert Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold">{alertSummary?.total || 0}</p>
              <p className="text-sm text-muted-foreground">Total Alerts</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-yellow-600">
                {alertSummary?.active || 0}
              </p>
              <p className="text-sm text-muted-foreground">Active</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-600">
                {alertSummary?.acknowledged || 0}
              </p>
              <p className="text-sm text-muted-foreground">Acknowledged</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">
                {alertSummary?.resolved || 0}
              </p>
              <p className="text-sm text-muted-foreground">Resolved</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}