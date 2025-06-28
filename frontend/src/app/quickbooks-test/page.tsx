'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function QuickBooksTestPage() {
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<any>(null)
  const [syncResult, setSyncResult] = useState<any>(null)
  const [metrics, setMetrics] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const checkStatus = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/api/default/quickbooks/status`)
      const data = await response.json()
      setStatus(data)
    } catch (err) {
      setError('Failed to check status')
    } finally {
      setLoading(false)
    }
  }

  const triggerSync = async () => {
    setLoading(true)
    setError(null)
    setSyncResult(null)
    try {
      const response = await fetch(`${API_BASE}/api/default/quickbooks/sync`, {
        method: 'POST'
      })
      const data = await response.json()
      setSyncResult(data)
      
      // Load metrics after sync
      await loadMetrics()
    } catch (err) {
      setError('Failed to trigger sync')
    } finally {
      setLoading(false)
    }
  }

  const loadMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/default/metrics`)
      const data = await response.json()
      setMetrics(data)
    } catch (err) {
      console.error('Failed to load metrics:', err)
    }
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8">QuickBooks Debug</h1>
      
      <div className="space-y-6">
        {/* Status Card */}
        <Card>
          <CardHeader>
            <CardTitle>Connection Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Button onClick={checkStatus} disabled={loading}>
                {loading ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Checking...</>
                ) : (
                  <>Check Status</>
                )}
              </Button>
              
              {status && (
                <div className="mt-4 space-y-2">
                  <div className="flex items-center gap-2">
                    {status.status === 'connected' ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-red-600" />
                    )}
                    <span className="font-medium">Status: {status.status}</span>
                  </div>
                  <div className="text-sm space-y-1">
                    <p>Realm ID: {status.realm_id || 'Not found'}</p>
                    <p>Token Valid: {status.token_valid ? 'Yes' : 'No'}</p>
                    <p>Last Synced: {status.last_synced || 'Never'}</p>
                    {status.last_error && (
                      <p className="text-red-600">Last Error: {status.last_error}</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Sync Card */}
        <Card>
          <CardHeader>
            <CardTitle>Manual Sync</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Button 
                onClick={triggerSync} 
                disabled={loading || status?.status !== 'connected'}
                variant="default"
              >
                {loading ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Syncing...</>
                ) : (
                  <><RefreshCw className="mr-2 h-4 w-4" /> Trigger Sync</>
                )}
              </Button>
              
              {syncResult && (
                <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded">
                  <p className="font-medium text-green-800">Sync Successful!</p>
                  <p className="text-sm text-green-700">
                    Records processed: {syncResult.records_processed}
                  </p>
                </div>
              )}
              
              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded">
                  <p className="text-red-800">{error}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Metrics Card */}
        {metrics && (
          <Card>
            <CardHeader>
              <CardTitle>Metrics ({metrics.count} total)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(metrics.metrics).map(([key, values]: [string, any]) => (
                  <div key={key} className="text-sm">
                    <span className="font-medium">{key}:</span> {values[0]?.value || 0}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}