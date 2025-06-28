'use client'

import { useState } from 'react'
import useSWR, { mutate } from 'swr'
import { formatDistanceToNow } from 'date-fns'
import { toast, Toaster } from 'react-hot-toast'
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { InsightsPanel } from '@/components/insights-panel'
import { 
  RefreshCw, 
  Download, 
  FileSpreadsheet, 
  Calendar,
  Loader2,
  AlertCircle,
  Lightbulb,
  X
} from 'lucide-react'

// API configuration
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// SWR fetcher
const fetcher = async (url: string) => {
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error('Failed to fetch')
  }
  return res.json()
}

// Type definitions
interface Template {
  name: string
  title: string
  description: string
  use_case: string
  refresh_frequency: string
  delivery_methods: string[]
  version: string
}

interface PopulatedFile {
  filename: string
  last_modified: string
  size: number
  url?: string
}

interface TemplateWithHistory extends Template {
  recent_files?: PopulatedFile[]
  last_generated?: string
}

export default function TemplatesPage() {
  const [refreshing, setRefreshing] = useState<string | null>(null)
  const [downloading, setDownloading] = useState<string | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  const [showInsights, setShowInsights] = useState(false)

  // Fetch templates list
  const { data, error, isLoading } = useSWR<{ templates: Template[] }>(
    `${API_BASE}/api/templates/`,
    fetcher,
    { refreshInterval: 30000 } // Refresh every 30 seconds
  )

  // Fetch history for each template
  const templatesWithHistory = useSWR<TemplateWithHistory[]>(
    data ? ['templates-with-history', data.templates] : null,
    async ([_, templates]) => {
      const withHistory = await Promise.all(
        templates.map(async (template) => {
          try {
            const history = await fetcher(`${API_BASE}/api/templates/${template.name}/history?limit=1`)
            return {
              ...template,
              recent_files: history.files,
              last_generated: history.files?.[0]?.last_modified
            }
          } catch {
            return template
          }
        })
      )
      return withHistory
    }
  )

  const handleRefresh = async (templateName: string) => {
    setRefreshing(templateName)
    
    try {
      const today = new Date()
      const startDate = new Date(today.getFullYear(), 0, 1) // Jan 1 of current year
      
      const response = await fetch(
        `${API_BASE}/api/templates/${templateName}/populate?` + 
        `start_date=${startDate.toISOString().split('T')[0]}&` +
        `end_date=${today.toISOString().split('T')[0]}`,
        { method: 'POST' }
      )

      if (!response.ok) {
        throw new Error(`Failed to refresh: ${response.statusText}`)
      }

      const result = await response.json()
      
      toast.success(`Successfully refreshed ${templateName}`, {
        duration: 5000,
        position: 'top-right'
      })

      // Refresh the data
      mutate(`${API_BASE}/api/templates/`)
      mutate(['templates-with-history', data?.templates])
      
    } catch (error) {
      toast.error(`Failed to refresh template: ${error instanceof Error ? error.message : 'Unknown error'}`, {
        duration: 5000,
        position: 'top-right'
      })
    } finally {
      setRefreshing(null)
    }
  }

  const handleDownload = async (template: TemplateWithHistory) => {
    setDownloading(template.name)
    
    try {
      if (!template.recent_files?.[0]) {
        toast.error('No file available to download. Please refresh first.', {
          duration: 4000,
          position: 'top-right'
        })
        return
      }

      const filename = template.recent_files[0].filename
      const response = await fetch(`${API_BASE}/api/templates/${template.name}/download/${filename}`)
      
      if (!response.ok) {
        throw new Error('Download failed')
      }

      // Create blob and download
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast.success('Download started', {
        duration: 3000,
        position: 'top-right'
      })
      
    } catch (error) {
      toast.error('Failed to download file', {
        duration: 4000,
        position: 'top-right'
      })
    } finally {
      setDownloading(null)
    }
  }

  const getFrequencyBadgeColor = (frequency: string) => {
    switch (frequency) {
      case 'daily': return 'bg-green-100 text-green-800'
      case 'weekly': return 'bg-blue-100 text-blue-800'
      case 'monthly': return 'bg-purple-100 text-purple-800'
      case 'on_demand': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              Error Loading Templates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">
              Failed to connect to the API. Please check if the backend is running.
            </p>
            <pre className="mt-2 text-sm text-gray-500">{API_BASE}/api/templates/</pre>
          </CardContent>
        </Card>
      </div>
    )
  }

  const templates = templatesWithHistory.data || data?.templates || []

  return (
    <div className="container mx-auto py-8 px-4">
      <Toaster />
      
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Financial Templates</h1>
        <p className="mt-2 text-gray-600">
          Refresh and download financial reports powered by live QuickBooks data
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {templates.map((template) => (
          <Card key={template.name} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <FileSpreadsheet className="h-8 w-8 text-blue-600" />
                <Badge className={getFrequencyBadgeColor(template.refresh_frequency)}>
                  {template.refresh_frequency.replace('_', ' ')}
                </Badge>
              </div>
              <CardTitle className="mt-4">{template.title}</CardTitle>
              <CardDescription className="mt-2">
                {template.description}
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-gray-600">
                  <span className="font-medium">Use case:</span>
                  <span>{template.use_case}</span>
                </div>
                
                {template.last_generated && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Calendar className="h-4 w-4" />
                    <span>
                      Last generated {formatDistanceToNow(new Date(template.last_generated), { addSuffix: true })}
                    </span>
                  </div>
                )}
                
                <div className="flex flex-wrap gap-1 mt-2">
                  {template.delivery_methods.map((method) => (
                    <Badge key={method} variant="outline" className="text-xs">
                      {method.replace('_', ' ')}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
            
            <CardFooter className="gap-2 flex-wrap">
              <div className="flex gap-2 flex-1">
                <Button
                  onClick={() => handleRefresh(template.name)}
                  disabled={refreshing === template.name}
                  className="flex-1"
                  variant="default"
                >
                {refreshing === template.name ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Refreshing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Refresh
                  </>
                )}
              </Button>
              
              <Button
                onClick={() => handleDownload(template)}
                disabled={downloading === template.name || !template.recent_files?.[0]}
                variant="outline"
                className="flex-1"
              >
                {downloading === template.name ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Downloading...
                  </>
                ) : (
                  <>
                    <Download className="mr-2 h-4 w-4" />
                    Download
                  </>
                )}
              </Button>
              </div>
              
              {template.recent_files?.[0] && (
                <Button
                  onClick={() => {
                    setSelectedTemplate(template.name)
                    setShowInsights(true)
                  }}
                  variant="outline"
                  size="sm"
                  className="w-full mt-2"
                >
                  <Lightbulb className="mr-2 h-4 w-4" />
                  View Insights
                </Button>
              )}
            </CardFooter>
          </Card>
        ))}
      </div>

      {templates.length === 0 && (
        <Card className="max-w-md mx-auto mt-8">
          <CardContent className="text-center py-8">
            <FileSpreadsheet className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No templates available yet.</p>
            <p className="text-sm text-gray-500 mt-2">
              Run `make template-register` to add templates.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Insights Panel Modal */}
      {showInsights && selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">
                {templates.find(t => t.name === selectedTemplate)?.title} - Insights
              </h2>
              <Button
                onClick={() => {
                  setShowInsights(false)
                  setSelectedTemplate(null)
                }}
                variant="ghost"
                size="sm"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              <InsightsPanel 
                templateName={selectedTemplate}
                onClose={() => {
                  setShowInsights(false)
                  setSelectedTemplate(null)
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}