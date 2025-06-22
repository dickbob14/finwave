import React, { useState, useEffect } from 'react';
import useSWR, { mutate } from 'swr';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  Upload, 
  Download, 
  RefreshCw, 
  TrendingUp, 
  TrendingDown,
  AlertCircle,
  Calculator
} from 'lucide-react';
import { fetcher } from '@/lib/utils';

interface Driver {
  driver_id: string;
  current_value: number;
  unit?: string;
  description?: string;
}

interface ScenarioPlannerProps {
  workspaceId: string;
}

export function ScenarioPlanner({ workspaceId }: ScenarioPlannerProps) {
  const [activeScenario, setActiveScenario] = useState('base');
  const [driverValues, setDriverValues] = useState<Record<string, number>>({});
  const [isUpdating, setIsUpdating] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  
  // Fetch current drivers
  const { data: drivers, error } = useSWR(
    `/api/${workspaceId}/forecast/drivers`,
    fetcher
  );
  
  // Initialize driver values
  useEffect(() => {
    if (drivers) {
      const values: Record<string, number> = {};
      drivers.forEach((driver: Driver) => {
        values[driver.driver_id] = driver.current_value;
      });
      setDriverValues(values);
    }
  }, [drivers]);
  
  const handleDriverChange = (driverId: string, value: number) => {
    setDriverValues(prev => ({
      ...prev,
      [driverId]: value
    }));
  };
  
  const applyScenario = async () => {
    setIsUpdating(true);
    
    try {
      // Create scenario with all driver updates
      const driverUpdates = Object.entries(driverValues).map(([driverId, value]) => ({
        driver_id: driverId,
        value
      }));
      
      const response = await fetch(`/api/${workspaceId}/forecast/scenarios`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_name: activeScenario,
          drivers: driverUpdates,
          regenerate_forecast: true
        })
      });
      
      if (!response.ok) throw new Error('Failed to apply scenario');
      
      const result = await response.json();
      
      // Refresh data
      mutate(`/api/${workspaceId}/forecast/drivers`);
      mutate(`/api/${workspaceId}/metrics/latest`);
      
      // Show success message
      alert(`Scenario applied! ${result.drivers_updated.length} drivers updated.`);
      
    } catch (error) {
      console.error('Error applying scenario:', error);
      alert('Failed to apply scenario');
    } finally {
      setIsUpdating(false);
    }
  };
  
  const handleFileUpload = async () => {
    if (!uploadFile) return;
    
    setIsUpdating(true);
    
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('scenario', activeScenario);
      
      const response = await fetch(`/api/${workspaceId}/forecast/upload`, {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) throw new Error('Failed to upload file');
      
      const result = await response.json();
      
      // Refresh drivers
      mutate(`/api/${workspaceId}/forecast/drivers`);
      
      alert(`Upload successful! Extracted ${result.drivers_extracted} drivers.`);
      setUploadFile(null);
      
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload file');
    } finally {
      setIsUpdating(false);
    }
  };
  
  const downloadTemplate = () => {
    window.open(`/api/forecast/download-template`, '_blank');
  };
  
  const formatDriverValue = (value: number, unit?: string) => {
    if (unit === 'percentage' || unit?.includes('percent')) {
      return `${value.toFixed(1)}%`;
    }
    return value.toLocaleString();
  };
  
  const getDriverIcon = (driverId: string) => {
    if (driverId.includes('growth') || driverId.includes('increase')) {
      return <TrendingUp className="h-4 w-4 text-green-600" />;
    }
    if (driverId.includes('churn') || driverId.includes('burn')) {
      return <TrendingDown className="h-4 w-4 text-red-600" />;
    }
    return <Calculator className="h-4 w-4 text-blue-600" />;
  };
  
  // Preset scenarios
  const applyPreset = (preset: 'conservative' | 'aggressive' | 'downside') => {
    const presets = {
      conservative: {
        new_customer_growth: 2,
        churn_rate: 1.5,
        headcount_growth: 0.5,
        gross_margin_target: 70
      },
      aggressive: {
        new_customer_growth: 5,
        churn_rate: 1,
        headcount_growth: 2,
        gross_margin_target: 75
      },
      downside: {
        new_customer_growth: 0.5,
        churn_rate: 3,
        headcount_growth: 0,
        gross_margin_target: 65
      }
    };
    
    const presetValues = presets[preset];
    setDriverValues(prev => ({
      ...prev,
      ...presetValues
    }));
    setActiveScenario(preset);
  };
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Scenario Planning</h2>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={downloadTemplate}>
            <Download className="h-4 w-4 mr-2" />
            Download Template
          </Button>
          <Button 
            onClick={applyScenario} 
            disabled={isUpdating}
            className="min-w-[120px]"
          >
            {isUpdating ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Updating...
              </>
            ) : (
              <>
                <Calculator className="h-4 w-4 mr-2" />
                Apply Scenario
              </>
            )}
          </Button>
        </div>
      </div>
      
      {/* Scenario Tabs */}
      <Tabs value={activeScenario} onValueChange={setActiveScenario}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="base">Base Case</TabsTrigger>
          <TabsTrigger value="conservative">Conservative</TabsTrigger>
          <TabsTrigger value="aggressive">Aggressive</TabsTrigger>
          <TabsTrigger value="downside">Downside</TabsTrigger>
        </TabsList>
        
        <TabsContent value={activeScenario} className="space-y-4 mt-4">
          {/* Quick Actions */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Adjust the drivers below to see how changes impact your forecast and runway.
              {activeScenario !== 'base' && (
                <Button
                  variant="link"
                  size="sm"
                  className="ml-2 p-0 h-auto"
                  onClick={() => applyPreset(activeScenario as any)}
                >
                  Apply {activeScenario} preset values
                </Button>
              )}
            </AlertDescription>
          </Alert>
          
          {/* Driver Controls */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* Revenue Drivers */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Revenue Drivers</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {drivers?.filter((d: Driver) => 
                  ['new_customer_growth', 'churn_rate', 'arpu', 'price_increase']
                  .includes(d.driver_id)
                ).map((driver: Driver) => (
                  <div key={driver.driver_id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="flex items-center gap-2">
                        {getDriverIcon(driver.driver_id)}
                        {driver.description || driver.driver_id}
                      </Label>
                      <Badge variant="secondary">
                        {formatDriverValue(driverValues[driver.driver_id] || 0, driver.unit)}
                      </Badge>
                    </div>
                    <Slider
                      value={[driverValues[driver.driver_id] || 0]}
                      onValueChange={([value]) => handleDriverChange(driver.driver_id, value)}
                      min={0}
                      max={driver.unit === 'percentage' ? 20 : 1000}
                      step={driver.unit === 'percentage' ? 0.1 : 10}
                      className="w-full"
                    />
                  </div>
                ))}
              </CardContent>
            </Card>
            
            {/* Cost Drivers */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Cost Drivers</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {drivers?.filter((d: Driver) => 
                  ['headcount_growth', 'salary_inflation', 'gross_margin_target', 'benefits_load']
                  .includes(d.driver_id)
                ).map((driver: Driver) => (
                  <div key={driver.driver_id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="flex items-center gap-2">
                        {getDriverIcon(driver.driver_id)}
                        {driver.description || driver.driver_id}
                      </Label>
                      <Badge variant="secondary">
                        {formatDriverValue(driverValues[driver.driver_id] || 0, driver.unit)}
                      </Badge>
                    </div>
                    <Slider
                      value={[driverValues[driver.driver_id] || 0]}
                      onValueChange={([value]) => handleDriverChange(driver.driver_id, value)}
                      min={0}
                      max={driver.unit === 'percentage' ? 100 : 1000}
                      step={driver.unit === 'percentage' ? 0.5 : 10}
                      className="w-full"
                    />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
          
          {/* Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Upload Driver Workbook</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <Input
                  type="file"
                  accept=".xlsx,.xlsm"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="flex-1"
                />
                <Button
                  onClick={handleFileUpload}
                  disabled={!uploadFile || isUpdating}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Upload
                </Button>
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                Upload an Excel file with DRIVER_ or BUDGET_ sheets to bulk update assumptions
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}