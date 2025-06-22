import React, { useState } from 'react';
import useSWR from 'swr';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { Calendar, DollarSign, TrendingUp, Users } from 'lucide-react';
import { fetcher } from '@/lib/utils';

interface ForecastComparisonProps {
  workspaceId: string;
}

interface ScenarioData {
  [metric: string]: {
    [date: string]: number;
  };
}

export function ForecastComparison({ workspaceId }: ForecastComparisonProps) {
  const [selectedMetric, setSelectedMetric] = useState('revenue');
  const [compareScenarios, setCompareScenarios] = useState(['conservative', 'aggressive']);
  
  // Fetch scenario comparison data
  const { data: comparison, isLoading } = useSWR(
    `/api/${workspaceId}/forecast/scenarios/compare?` +
    `base_scenario=base&compare_scenarios=${compareScenarios.join(',')}&` +
    `metrics=${selectedMetric},burn_rate,runway_months`,
    fetcher
  );
  
  // Transform data for charts
  const getChartData = () => {
    if (!comparison?.scenarios) return [];
    
    const dates = new Set<string>();
    Object.values(comparison.scenarios).forEach((scenario: ScenarioData) => {
      if (scenario[selectedMetric]) {
        Object.keys(scenario[selectedMetric]).forEach(date => dates.add(date));
      }
    });
    
    const sortedDates = Array.from(dates).sort();
    
    return sortedDates.map(date => {
      const dataPoint: any = { date: new Date(date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }) };
      
      Object.entries(comparison.scenarios).forEach(([scenarioName, scenarioData]: [string, ScenarioData]) => {
        dataPoint[scenarioName] = scenarioData[selectedMetric]?.[date] || 0;
      });
      
      return dataPoint;
    });
  };
  
  // Calculate impact summary
  const getImpactSummary = () => {
    if (!comparison?.scenarios) return null;
    
    const base = comparison.scenarios['base'];
    const impacts: any[] = [];
    
    compareScenarios.forEach(scenario => {
      const scenarioData = comparison.scenarios[scenario];
      if (!scenarioData || !base) return;
      
      // Get last value for each metric
      const getLastValue = (data: any, metric: string) => {
        const values = Object.values(data[metric] || {}) as number[];
        return values[values.length - 1] || 0;
      };
      
      const baseRevenue = getLastValue(base, 'revenue');
      const scenarioRevenue = getLastValue(scenarioData, 'revenue');
      const revenueImpact = ((scenarioRevenue - baseRevenue) / baseRevenue) * 100;
      
      const baseRunway = getLastValue(base, 'runway_months');
      const scenarioRunway = getLastValue(scenarioData, 'runway_months');
      const runwayImpact = scenarioRunway - baseRunway;
      
      impacts.push({
        scenario,
        revenueImpact,
        runwayImpact,
        finalRevenue: scenarioRevenue,
        finalRunway: scenarioRunway
      });
    });
    
    return impacts;
  };
  
  const formatValue = (value: number, metric: string) => {
    if (metric.includes('revenue') || metric.includes('burn')) {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);
    }
    if (metric.includes('months')) {
      return `${value.toFixed(1)} months`;
    }
    return value.toLocaleString();
  };
  
  const impacts = getImpactSummary();
  const chartData = getChartData();
  
  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Scenario Impact Analysis</h3>
        <Select value={selectedMetric} onValueChange={setSelectedMetric}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Select metric" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="revenue">Revenue</SelectItem>
            <SelectItem value="burn_rate">Burn Rate</SelectItem>
            <SelectItem value="runway_months">Runway</SelectItem>
            <SelectItem value="gross_margin">Gross Margin</SelectItem>
            <SelectItem value="headcount">Headcount</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      {/* Impact Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {impacts?.map(impact => (
          <Card key={impact.scenario}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                {impact.scenario.charAt(0).toUpperCase() + impact.scenario.slice(1)} Scenario
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Revenue Impact</span>
                  <Badge variant={impact.revenueImpact > 0 ? 'default' : 'destructive'}>
                    {impact.revenueImpact > 0 ? '+' : ''}{impact.revenueImpact.toFixed(1)}%
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Runway Impact</span>
                  <Badge variant={impact.runwayImpact > 0 ? 'default' : 'destructive'}>
                    {impact.runwayImpact > 0 ? '+' : ''}{impact.runwayImpact.toFixed(1)} mo
                  </Badge>
                </div>
                <div className="pt-2 border-t">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Final Revenue</span>
                    <span className="font-medium">{formatValue(impact.finalRevenue, 'revenue')}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm mt-1">
                    <span className="text-muted-foreground">Final Runway</span>
                    <span className="font-medium">{impact.finalRunway.toFixed(1)} months</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {/* Forecast Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Forecast Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="h-[400px] flex items-center justify-center">
              <p className="text-muted-foreground">Loading forecast data...</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis tickFormatter={(value) => formatValue(value, selectedMetric)} />
                <Tooltip formatter={(value: number) => formatValue(value, selectedMetric)} />
                <Legend />
                
                <Line
                  type="monotone"
                  dataKey="base"
                  stroke="#8884d8"
                  strokeWidth={2}
                  name="Base Case"
                />
                
                {compareScenarios.map((scenario, idx) => (
                  <Line
                    key={scenario}
                    type="monotone"
                    dataKey={scenario}
                    stroke={idx === 0 ? '#82ca9d' : '#ff7c7c'}
                    strokeWidth={2}
                    strokeDasharray={idx === 0 ? '0' : '5 5'}
                    name={scenario.charAt(0).toUpperCase() + scenario.slice(1)}
                  />
                ))}
                
                {/* Add reference line for current date */}
                <ReferenceLine
                  x={new Date().toLocaleDateString('en-US', { month: 'short', year: '2-digit' })}
                  stroke="#666"
                  strokeDasharray="3 3"
                  label="Today"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
      
      {/* Key Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Key Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {impacts?.map(impact => (
              <li key={impact.scenario} className="flex items-start gap-2">
                <span className="text-sm">•</span>
                <span className="text-sm">
                  <strong>{impact.scenario}</strong> scenario: 
                  {impact.revenueImpact > 0 ? ' increases' : ' decreases'} revenue by{' '}
                  <span className={impact.revenueImpact > 0 ? 'text-green-600' : 'text-red-600'}>
                    {Math.abs(impact.revenueImpact).toFixed(1)}%
                  </span>
                  {impact.runwayImpact !== 0 && (
                    <> and {impact.runwayImpact > 0 ? 'extends' : 'shortens'} runway by{' '}
                    <span className={impact.runwayImpact > 0 ? 'text-green-600' : 'text-red-600'}>
                      {Math.abs(impact.runwayImpact).toFixed(1)} months
                    </span>
                    </>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}