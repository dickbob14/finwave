import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScenarioPlanner } from '@/components/scenario-planner';
import { ForecastComparison } from '@/components/forecast-comparison';
import { DashboardWithVariance } from '@/pages/dashboard-with-variance';
import { Calculator, LineChart, AlertCircle } from 'lucide-react';

interface ScenarioPlanningPageProps {
  workspaceId: string;
}

export function ScenarioPlanningPage({ workspaceId }: ScenarioPlanningPageProps) {
  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Scenario Planning</h1>
          <p className="text-muted-foreground mt-1">
            Adjust key drivers to see how changes impact your forecast and runway
          </p>
        </div>
      </div>
      
      <Tabs defaultValue="drivers" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="drivers" className="flex items-center gap-2">
            <Calculator className="h-4 w-4" />
            Driver Modeling
          </TabsTrigger>
          <TabsTrigger value="comparison" className="flex items-center gap-2">
            <LineChart className="h-4 w-4" />
            Scenario Comparison
          </TabsTrigger>
          <TabsTrigger value="impact" className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            Impact Dashboard
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="drivers" className="space-y-4">
          <ScenarioPlanner workspaceId={workspaceId} />
        </TabsContent>
        
        <TabsContent value="comparison" className="space-y-4">
          <ForecastComparison workspaceId={workspaceId} />
        </TabsContent>
        
        <TabsContent value="impact" className="space-y-4">
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
              <h3 className="font-medium mb-2">Variance Alerts from Scenario Changes</h3>
              <p className="text-sm text-muted-foreground">
                The dashboard below shows real-time variance alerts based on your scenario adjustments.
                Red badges indicate metrics that have breached thresholds under the current scenario.
              </p>
            </div>
            <DashboardWithVariance workspaceId={workspaceId} />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}