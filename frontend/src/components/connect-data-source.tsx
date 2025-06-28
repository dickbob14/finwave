import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import useSWR, { mutate } from 'swr';
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
  RefreshCw,
  Settings
} from 'lucide-react';
import { fetcher } from '@/lib/utils';
import { OAuthConfigDialog } from './oauth-config-dialog';

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
  const router = useRouter();
  const [step, setStep] = useState<'select' | 'connecting' | 'success' | 'error'>('select');
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [syncProgress, setSyncProgress] = useState(0);
  const [showOAuthConfig, setShowOAuthConfig] = useState(false);
  const [configureSource, setConfigureSource] = useState<string | null>(null);
  
  // Fetch existing integrations
  const { data: integrations, mutate: refreshIntegrations } = useSWR<Integration[]>(
    open ? `/api/${workspaceId}/oauth/integrations` : null,
    fetcher
  );
  
  // Fetch OAuth configurations
  const { data: oauthConfigs } = useSWR(
    open ? `/api/${workspaceId}/oauth/config/list` : null,
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
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': 'Bearer demo-token' // Demo token for BYPASS_AUTH mode
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        if (errorData.detail?.includes('not configured')) {
          // OAuth not configured, show configuration dialog
          setStep('select');
          setConfigureSource(sourceId);
          setShowOAuthConfig(true);
          return;
        }
        throw new Error(errorData.detail || 'Failed to initiate connection');
      }
      
      const data = await response.json();
      
      // Open OAuth in new tab instead of popup
      window.open(data.auth_url, '_blank');
      
      // Don't poll - instead show a message to check back
      setTimeout(() => {
        setStep('select');
        refreshIntegrations();
      }, 3000);
      
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
        method: 'POST',
        headers: {
          'Authorization': 'Bearer demo-token' // Demo token for BYPASS_AUTH mode
        }
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
                const oauthConfig = oauthConfigs?.find((c: any) => c.source === source.id);
                const isConfigured = oauthConfig?.is_configured;
                
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
                              {!isConnected && !isConfigured && (
                                <Badge variant="secondary" className="ml-2">
                                  Setup Required
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
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setConfigureSource(source.id);
                                setShowOAuthConfig(true);
                              }}
                            >
                              <Settings className="h-4 w-4 mr-2" />
                              Configure
                            </Button>
                            <Button 
                              onClick={() => handleConnect(source.id)}
                              disabled={!isConfigured && source.id !== 'google_sheets'}
                            >
                              Connect
                            </Button>
                          </div>
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
                Complete the authorization in the new tab that just opened
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                This dialog will automatically refresh when done
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
                router.push('/dashboard');
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
    <>
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
      
      {configureSource && (
        <OAuthConfigDialog
          open={showOAuthConfig}
          onOpenChange={setShowOAuthConfig}
          workspaceId={workspaceId}
          source={configureSource}
          onConfigured={() => {
            setShowOAuthConfig(false);
            setConfigureSource(null);
            // Refresh OAuth configs
            mutate(`/api/${workspaceId}/oauth/config/list`);
          }}
        />
      )}
    </>
  );
}