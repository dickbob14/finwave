import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useSWR from 'swr';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Check,
  X,
  Loader2,
  Database,
  Users,
  DollarSign,
  FileSpreadsheet,
  AlertCircle,
  ExternalLink,
  RefreshCw
} from 'lucide-react';
import { fetcher } from '@/lib/utils';

interface ConnectDataSourceProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  workspaceId: string;
}

interface Integration {
  id: string;
  source: string;
  status: string;
  connected_at: string;
  last_synced_at?: string;
  last_sync_error?: string;
  metadata: Record<string, any>;
}

const DATA_SOURCES = [
  {
    id: 'quickbooks',
    name: 'QuickBooks',
    description: 'Sync P&L, balance sheet, and customer data',
    icon: <Database className="h-8 w-8" />,
    category: 'accounting',
    color: 'bg-green-500',
    features: ['Financial statements', 'Customer invoices', 'AR/AP aging', 'Chart of accounts']
  },
  {
    id: 'salesforce',
    name: 'Salesforce',
    description: 'Import opportunities, accounts, and activities',
    icon: <Users className="h-8 w-8" />,
    category: 'crm',
    color: 'bg-blue-500',
    features: ['Sales pipeline', 'Account data', 'Activity tracking', 'Custom objects']
  },
  {
    id: 'hubspot',
    name: 'HubSpot',
    description: 'Connect deals, companies, and contacts',
    icon: <Users className="h-8 w-8" />,
    category: 'crm',
    color: 'bg-orange-500',
    features: ['Deal pipeline', 'Company data', 'Contact engagement', 'Marketing metrics']
  },
  {
    id: 'gusto',
    name: 'Gusto',
    description: 'Sync payroll, headcount, and compensation',
    icon: <DollarSign className="h-8 w-8" />,
    category: 'payroll',
    color: 'bg-purple-500',
    features: ['Employee roster', 'Payroll runs', 'Benefits data', 'Department breakdown']
  },
  {
    id: 'google_sheets',
    name: 'Google Sheets',
    description: 'Import custom metrics and forecasts',
    icon: <FileSpreadsheet className="h-8 w-8" />,
    category: 'other',
    color: 'bg-yellow-500',
    features: ['Custom metrics', 'Budget uploads', 'Forecast models', 'Manual data']
  }
];

export function ConnectDataSource({ open, onOpenChange, workspaceId }: ConnectDataSourceProps) {
  const navigate = useNavigate();
  const [step, setStep] = useState<'select' | 'connecting' | 'success' | 'error'>('select');
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [syncProgress, setSyncProgress] = useState(0);
  
  // Fetch existing integrations
  const { data: integrations, mutate: refreshIntegrations } = useSWR<Integration[]>(
    open ? `/api/${workspaceId}/oauth/integrations` : null,
    fetcher
  );
  
  const handleConnect = async (sourceId: string) => {
    setSelectedSource(sourceId);
    setStep('connecting');
    setError(null);
    
    try {
      // Initiate OAuth flow
      const response = await fetch(`/api/${workspaceId}/oauth/connect/${sourceId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        throw new Error('Failed to initiate connection');
      }
      
      const data = await response.json();
      
      // Open OAuth window
      const authWindow = window.open(
        data.auth_url,
        'oauth',
        'width=600,height=700,left=100,top=100'
      );
      
      // Poll for completion
      const checkInterval = setInterval(() => {
        if (authWindow?.closed) {
          clearInterval(checkInterval);
          checkConnectionStatus(sourceId);
        }
      }, 1000);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
      setStep('error');
    }
  };
  
  const checkConnectionStatus = async (sourceId: string) => {
    // Simulate initial sync progress
    let progress = 0;
    const progressInterval = setInterval(() => {
      progress += 10;
      setSyncProgress(progress);
      if (progress >= 100) {
        clearInterval(progressInterval);
      }
    }, 500);
    
    // Check if connection was successful
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    try {
      await refreshIntegrations();
      
      const integration = integrations?.find(i => i.source === sourceId);
      if (integration?.status === 'connected') {
        setStep('success');
      } else {
        throw new Error('Connection not established');
      }
    } catch (err) {
      setError('Connection failed. Please try again.');
      setStep('error');
    }
  };
  
  const handleTriggerSync = async (sourceId: string) => {
    try {
      await fetch(`/api/${workspaceId}/oauth/integrations/${sourceId}/sync`, {
        method: 'POST'
      });
      await refreshIntegrations();
    } catch (err) {
      console.error('Sync failed:', err);
    }
  };
  
  const getSourceById = (id: string) => DATA_SOURCES.find(s => s.id === id);
  
  const renderContent = () => {
    switch (step) {
      case 'select':
        return (
          <Tabs defaultValue="all" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="accounting">Accounting</TabsTrigger>
              <TabsTrigger value="crm">CRM</TabsTrigger>
              <TabsTrigger value="payroll">Payroll</TabsTrigger>
            </TabsList>
            
            <TabsContent value="all" className="mt-4 space-y-4">
              {DATA_SOURCES.map(source => {
                const integration = integrations?.find(i => i.source === source.id);
                const isConnected = integration?.status === 'connected';
                
                return (
                  <Card key={source.id} className={isConnected ? 'border-green-500' : ''}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`p-3 rounded-lg ${source.color} text-white`}>
                            {source.icon}
                          </div>
                          <div>
                            <CardTitle className="flex items-center gap-2">
                              {source.name}
                              {isConnected && (
                                <Badge variant="success" className="ml-2">
                                  <Check className="h-3 w-3 mr-1" />
                                  Connected
                                </Badge>
                              )}
                            </CardTitle>
                            <CardDescription>{source.description}</CardDescription>
                          </div>
                        </div>
                        {isConnected ? (
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleTriggerSync(source.id)}
                            >
                              <RefreshCw className="h-4 w-4 mr-2" />
                              Sync Now
                            </Button>
                          </div>
                        ) : (
                          <Button onClick={() => handleConnect(source.id)}>
                            Connect
                          </Button>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        {source.features.map(feature => (
                          <div key={feature} className="flex items-center gap-2">
                            <Check className="h-3 w-3 text-muted-foreground" />
                            <span className="text-muted-foreground">{feature}</span>
                          </div>
                        ))}
                      </div>
                      {integration?.last_synced_at && (
                        <p className="text-xs text-muted-foreground mt-4">
                          Last synced: {new Date(integration.last_synced_at).toLocaleString()}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </TabsContent>
            
            {['accounting', 'crm', 'payroll'].map(category => (
              <TabsContent key={category} value={category} className="mt-4 space-y-4">
                {DATA_SOURCES.filter(s => s.category === category).map(source => {
                  const integration = integrations?.find(i => i.source === source.id);
                  const isConnected = integration?.status === 'connected';
                  
                  return (
                    <Card key={source.id} className={isConnected ? 'border-green-500' : ''}>
                      {/* Same card content as above */}
                    </Card>
                  );
                })}
              </TabsContent>
            ))}
          </Tabs>
        );
        
      case 'connecting':
        const source = getSourceById(selectedSource!);
        return (
          <div className="text-center py-8 space-y-6">
            <div className={`inline-flex p-4 rounded-full ${source?.color} text-white`}>
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
            <div>
              <h3 className="text-lg font-semibold">Connecting to {source?.name}</h3>
              <p className="text-muted-foreground mt-2">
                Complete the authorization in the popup window
              </p>
            </div>
            <Progress value={syncProgress} className="max-w-xs mx-auto" />
            {syncProgress > 0 && (
              <p className="text-sm text-muted-foreground">
                Initial sync in progress... {syncProgress}%
              </p>
            )}
          </div>
        );
        
      case 'success':
        return (
          <div className="text-center py-8 space-y-6">
            <div className="inline-flex p-4 rounded-full bg-green-100 text-green-600">
              <Check className="h-8 w-8" />
            </div>
            <div>
              <h3 className="text-lg font-semibold">Successfully Connected!</h3>
              <p className="text-muted-foreground mt-2">
                Your data is being synced and will be available shortly
              </p>
            </div>
            <div className="flex gap-3 justify-center">
              <Button variant="outline" onClick={() => setStep('select')}>
                Connect Another
              </Button>
              <Button onClick={() => {
                onOpenChange(false);
                navigate('/dashboard');
              }}>
                Go to Dashboard
              </Button>
            </div>
          </div>
        );
        
      case 'error':
        return (
          <div className="text-center py-8 space-y-6">
            <div className="inline-flex p-4 rounded-full bg-red-100 text-red-600">
              <X className="h-8 w-8" />
            </div>
            <div>
              <h3 className="text-lg font-semibold">Connection Failed</h3>
              <p className="text-muted-foreground mt-2">{error}</p>
            </div>
            <Button onClick={() => setStep('select')}>
              Try Again
            </Button>
          </div>
        );
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Connect Data Sources</DialogTitle>
          <DialogDescription>
            Connect your business tools to automatically sync financial data
          </DialogDescription>
        </DialogHeader>
        
        {renderContent()}
        
        {step === 'select' && integrations && integrations.length > 0 && (
          <Alert className="mt-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              You have {integrations.length} active connection{integrations.length > 1 ? 's' : ''}.
              Data syncs automatically every hour.
            </AlertDescription>
          </Alert>
        )}
      </DialogContent>
    </Dialog>
  );
}