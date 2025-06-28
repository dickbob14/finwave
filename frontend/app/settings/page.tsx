"use client"

import type React from "react"

import { useState, useEffect } from "react"
import useSWR from "swr"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ConnectorWizard } from "@/components/ConnectorWizard"
import { Badge } from "@/components/ui/badge"
import { Upload, Settings, Database, Users } from "lucide-react"

const fetcher = (url: string) => fetch(url, {
  headers: {
    'Authorization': 'Bearer demo-token'
  }
}).then(res => res.json())

export default function SettingsPage() {
  const [workspaceName, setWorkspaceName] = useState("My Company")
  const [logoFile, setLogoFile] = useState<File | null>(null)
  
  // Fetch real integration data with auto-refresh
  const { data: integrations, mutate: refreshIntegrations } = useSWR("/api/default/oauth/integrations", fetcher, {
    refreshInterval: 5000 // Poll every 5 seconds
  })
  
  // Handle OAuth callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('oauth_success')) {
      const source = params.get('source')
      console.log(`OAuth success for ${source}`)
      refreshIntegrations()
      // Clean up URL
      window.history.replaceState({}, '', '/settings')
    } else if (params.get('oauth_error')) {
      console.error('OAuth error:', params.get('description'))
      // Clean up URL
      window.history.replaceState({}, '', '/settings')
    }
  }, [])

  const handleLogoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setLogoFile(file)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-primary">Settings</h1>
        <p className="text-muted-foreground mt-2">Manage your workspace and data connections</p>
      </div>

      <Tabs defaultValue="workspace" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="workspace">Workspace</TabsTrigger>
          <TabsTrigger value="integrations">Data Sources</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
        </TabsList>

        <TabsContent value="workspace" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="w-5 h-5 mr-2" />
                Workspace Settings
              </CardTitle>
              <CardDescription>Configure your workspace name and branding</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="workspace-name">Workspace Name</Label>
                <Input
                  id="workspace-name"
                  value={workspaceName}
                  onChange={(e) => setWorkspaceName(e.target.value)}
                  placeholder="Enter workspace name"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="logo-upload">Company Logo</Label>
                <div className="flex items-center space-x-4">
                  <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center">
                    {logoFile ? (
                      <img
                        src={URL.createObjectURL(logoFile) || "/placeholder.svg"}
                        alt="Logo"
                        className="w-full h-full object-cover rounded-lg"
                      />
                    ) : (
                      <Upload className="w-6 h-6 text-muted-foreground" />
                    )}
                  </div>
                  <div className="flex-1">
                    <Input
                      id="logo-upload"
                      type="file"
                      accept="image/*"
                      onChange={handleLogoUpload}
                      className="cursor-pointer"
                    />
                    <p className="text-xs text-muted-foreground mt-1">PNG, JPG up to 2MB</p>
                  </div>
                </div>
              </div>

              <Button className="bg-secondary hover:bg-secondary/90">Save Changes</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="integrations" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Database className="w-5 h-5 mr-2" />
                Data Source Connections
              </CardTitle>
              <CardDescription>Connect and manage your data sources</CardDescription>
            </CardHeader>
            <CardContent>
              <ConnectorWizard />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Connected Sources</CardTitle>
              <CardDescription>Currently active data connections</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {integrations && integrations.length > 0 ? (
                  integrations.map((integration: any) => (
                    <div key={integration.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">
                          {integration.source === 'quickbooks' ? '📊' : 
                           integration.source === 'salesforce' ? '☁️' :
                           integration.source === 'hubspot' ? '🟠' : '📊'}
                        </span>
                        <div>
                          <h4 className="font-semibold">
                            {integration.source === 'quickbooks' ? 'QuickBooks Online' :
                             integration.source === 'salesforce' ? 'Salesforce' :
                             integration.source === 'hubspot' ? 'HubSpot' :
                             integration.source}
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            {integration.last_synced_at 
                              ? `Last sync: ${new Date(integration.last_synced_at).toLocaleString()}`
                              : 'Not synced yet'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge className={`${
                          integration.status === 'connected' ? 'bg-success text-white' :
                          integration.status === 'error' ? 'bg-error text-white' :
                          'bg-warning text-white'
                        }`}>
                          {integration.status === 'connected' ? 'Active' :
                           integration.status === 'error' ? 'Error' :
                           'Pending'}
                        </Badge>
                        <Button variant="outline" size="sm">
                          Disconnect
                        </Button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    No data sources connected yet. Use the connector wizard above to get started.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="users" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Users className="w-5 h-5 mr-2" />
                User Management
              </CardTitle>
              <CardDescription>Manage workspace users and permissions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h4 className="font-semibold">Team Members</h4>
                  <Button size="sm">Invite User</Button>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center text-sm font-semibold">
                        JD
                      </div>
                      <div>
                        <p className="font-medium">John Doe</p>
                        <p className="text-sm text-muted-foreground">john@company.com</p>
                      </div>
                    </div>
                    <Badge>Admin</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="advanced" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Advanced Settings</CardTitle>
              <CardDescription>Advanced configuration options</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>API Endpoint</Label>
                <Input value={process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"} disabled />
                <p className="text-xs text-muted-foreground">Backend API endpoint (read-only)</p>
              </div>

              <div className="space-y-2">
                <Label>Data Refresh Interval</Label>
                <select className="w-full p-2 border rounded-md">
                  <option value="5">5 minutes</option>
                  <option value="15">15 minutes</option>
                  <option value="30">30 minutes</option>
                  <option value="60">1 hour</option>
                </select>
              </div>

              <Button variant="outline" className="text-error border-error hover:bg-error hover:text-white">
                Reset Workspace
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
