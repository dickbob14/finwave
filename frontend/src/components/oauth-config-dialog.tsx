import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  ExternalLink,
  Info,
  Lock,
  AlertCircle,
  Check,
  Loader2
} from 'lucide-react';

interface OAuthConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  workspaceId: string;
  source: string;
  onConfigured?: () => void;
}

const OAUTH_SETUP_GUIDES = {
  quickbooks: {
    name: 'QuickBooks',
    developerUrl: 'https://developer.intuit.com',
    steps: [
      'Go to the Intuit Developer Dashboard',
      'Create a new app or select an existing one',
      'Add OAuth 2.0 redirect URI: http://localhost:8000/api/oauth/callback',
      'Copy your Client ID and Client Secret',
      'Select "Accounting" scope for your app'
    ],
    scopes: ['com.intuit.quickbooks.accounting'],
    testInfo: 'Use sandbox mode for testing with sample data'
  },
  salesforce: {
    name: 'Salesforce',
    developerUrl: 'https://developer.salesforce.com',
    steps: [
      'Go to Salesforce Setup > App Manager',
      'Create a new Connected App',
      'Enable OAuth Settings',
      'Add callback URL: http://localhost:8000/api/oauth/callback',
      'Select required OAuth scopes (api, refresh_token)',
      'Copy Consumer Key (Client ID) and Consumer Secret'
    ],
    scopes: ['api', 'refresh_token'],
    testInfo: 'Use a Developer Edition org for testing'
  },
  hubspot: {
    name: 'HubSpot',
    developerUrl: 'https://developers.hubspot.com',
    steps: [
      'Go to HubSpot App Dashboard',
      'Create a new app',
      'Navigate to Auth settings',
      'Add redirect URL: http://localhost:8000/api/oauth/callback',
      'Copy App ID (Client ID) and Client Secret',
      'Select CRM scopes for contacts, companies, and deals'
    ],
    scopes: ['crm.objects.contacts.read', 'crm.objects.companies.read', 'crm.objects.deals.read'],
    testInfo: 'Use a test portal for development'
  },
  gusto: {
    name: 'Gusto',
    developerUrl: 'https://dev.gusto.com',
    steps: [
      'Go to Gusto Developer Portal',
      'Create a new application',
      'Set redirect URI: http://localhost:8000/api/oauth/callback',
      'Copy Client ID and Client Secret',
      'Request production access when ready'
    ],
    scopes: ['public'],
    testInfo: 'Use demo mode for testing'
  }
};

export function OAuthConfigDialog({
  open,
  onOpenChange,
  workspaceId,
  source,
  onConfigured
}: OAuthConfigDialogProps) {
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [environment, setEnvironment] = useState('production');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const guide = OAUTH_SETUP_GUIDES[source as keyof typeof OAUTH_SETUP_GUIDES];
  
  if (!guide) {
    return null;
  }

  const handleSave = async () => {
    if (!clientId || !clientSecret) {
      setError('Please enter both Client ID and Client Secret');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/${workspaceId}/oauth/config/configure`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': 'Bearer demo-token' // Demo token for BYPASS_AUTH mode
        },
        body: JSON.stringify({
          source,
          client_id: clientId,
          client_secret: clientSecret,
          environment
        })
      });

      if (!response.ok) {
        throw new Error('Failed to save OAuth configuration');
      }

      setSuccess(true);
      setTimeout(() => {
        onConfigured?.();
        onOpenChange(false);
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Configuration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Configure {guide.name} OAuth</DialogTitle>
          <DialogDescription>
            Set up your OAuth app credentials to connect with {guide.name}
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="credentials" className="mt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="credentials">Credentials</TabsTrigger>
            <TabsTrigger value="guide">Setup Guide</TabsTrigger>
          </TabsList>

          <TabsContent value="credentials" className="space-y-4 mt-4">
            {success ? (
              <Alert className="border-green-500">
                <Check className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-600">
                  OAuth credentials saved successfully!
                </AlertDescription>
              </Alert>
            ) : (
              <>
                <Alert>
                  <Lock className="h-4 w-4" />
                  <AlertDescription>
                    Your credentials are encrypted and stored securely. They are never shared or exposed.
                  </AlertDescription>
                </Alert>

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="client-id">Client ID</Label>
                    <Input
                      id="client-id"
                      type="text"
                      value={clientId}
                      onChange={(e) => setClientId(e.target.value)}
                      placeholder="Enter your OAuth Client ID"
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="client-secret">Client Secret</Label>
                    <Input
                      id="client-secret"
                      type="password"
                      value={clientSecret}
                      onChange={(e) => setClientSecret(e.target.value)}
                      placeholder="Enter your OAuth Client Secret"
                      className="mt-1"
                    />
                  </div>

                  <div>
                    <Label htmlFor="environment">Environment</Label>
                    <select
                      id="environment"
                      value={environment}
                      onChange={(e) => setEnvironment(e.target.value)}
                      className="w-full mt-1 px-3 py-2 border rounded-md"
                    >
                      <option value="production">Production</option>
                      <option value="sandbox">Sandbox/Development</option>
                    </select>
                  </div>
                </div>

                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
              </>
            )}
          </TabsContent>

          <TabsContent value="guide" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  Setup Instructions
                  <Button variant="outline" size="sm" asChild>
                    <a href={guide.developerUrl} target="_blank" rel="noopener noreferrer">
                      Developer Portal
                      <ExternalLink className="h-3 w-3 ml-2" />
                    </a>
                  </Button>
                </CardTitle>
                <CardDescription>
                  Follow these steps to create your {guide.name} OAuth app
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ol className="space-y-3">
                  {guide.steps.map((step, index) => (
                    <li key={index} className="flex gap-3">
                      <span className="flex-shrink-0 w-6 h-6 bg-primary/10 text-primary rounded-full flex items-center justify-center text-sm font-medium">
                        {index + 1}
                      </span>
                      <span className="text-sm">{step}</span>
                    </li>
                  ))}
                </ol>

                <div className="mt-6 space-y-4">
                  <div>
                    <h4 className="font-medium text-sm mb-2">Required Scopes</h4>
                    <div className="flex flex-wrap gap-2">
                      {guide.scopes.map(scope => (
                        <code key={scope} className="text-xs bg-muted px-2 py-1 rounded">
                          {scope}
                        </code>
                      ))}
                    </div>
                  </div>

                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription className="text-sm">
                      {guide.testInfo}
                    </AlertDescription>
                  </Alert>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading || success}>
            {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            {success ? 'Saved!' : 'Save Credentials'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}