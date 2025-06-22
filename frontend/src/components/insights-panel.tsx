'use client'

import { useState } from 'react'
import useSWR from 'swr'
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Lightbulb, 
  TrendingUp, 
  TrendingDown,
  AlertCircle,
  CheckCircle,
  RefreshCw,
  Loader2,
  ChevronRight
} from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const fetcher = async (url: string) => {
  const res = await fetch(url)
  if (!res.ok) throw new Error('Failed to fetch')
  return res.json()
}

interface Insight {
  summary: string
  narrative: string
  findings: Array<{
    type: string
    metric: string
    significance: string
    direction?: string
    change_pct?: number
    value?: number
    assessment?: string
  }>
  recommendations: string[]
  generated_at: string
}

interface InsightsPanelProps {
  templateName: string
  onClose?: () => void
}

export function InsightsPanel({ templateName, onClose }: InsightsPanelProps) {
  const [isRefreshing, setIsRefreshing] = useState(false)
  
  const { data, error, isLoading, mutate } = useSWR<Insight>(
    `${API_BASE}/insights/${templateName}`,
    fetcher
  )

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      const response = await fetch(
        `${API_BASE}/insights/${templateName}/generate?refresh_data=true`,
        { method: 'POST' }
      )
      
      if (response.ok) {
        const result = await response.json()
        mutate(result.insights)
      }
    } catch (error) {
      console.error('Failed to refresh insights:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  const getIcon = (finding: any) => {
    if (finding.direction === 'positive' || finding.assessment === 'strong') {
      return <TrendingUp className="h-4 w-4 text-green-600" />
    } else if (finding.direction === 'negative' || finding.assessment === 'weak') {
      return <TrendingDown className="h-4 w-4 text-red-600" />
    } else if (finding.significance === 'high') {
      return <AlertCircle className="h-4 w-4 text-amber-600" />
    }
    return <CheckCircle className="h-4 w-4 text-blue-600" />
  }

  const getSignificanceBadge = (significance: string) => {
    const colors = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-amber-100 text-amber-800',
      low: 'bg-green-100 text-green-800'
    }
    return (
      <Badge className={colors[significance as keyof typeof colors] || colors.low}>
        {significance}
      </Badge>
    )
  }

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </CardContent>
      </Card>
    )
  }

  if (error || !data) {
    return (
      <Card className="w-full">
        <CardContent className="py-8">
          <div className="text-center">
            <AlertCircle className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-600">No insights available</p>
            <Button 
              onClick={handleRefresh} 
              variant="outline" 
              size="sm" 
              className="mt-4"
            >
              Generate Insights
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-amber-600" />
            <CardTitle>AI Insights</CardTitle>
          </div>
          <Button
            onClick={isRefreshing ? undefined : handleRefresh}
            disabled={isRefreshing}
            variant="ghost"
            size="sm"
          >
            {isRefreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>
        </div>
        <CardDescription>
          {data.summary}
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Narrative */}
        <div className="prose prose-sm max-w-none">
          <p className="text-gray-700 leading-relaxed">
            {data.narrative}
          </p>
        </div>

        {/* Key Findings */}
        {data.findings.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Key Findings</h4>
            <div className="space-y-2">
              {data.findings.map((finding, idx) => (
                <div 
                  key={idx} 
                  className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg"
                >
                  <div className="mt-0.5">{getIcon(finding)}</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm">{finding.metric}</span>
                      {getSignificanceBadge(finding.significance)}
                    </div>
                    <p className="text-sm text-gray-600">
                      {finding.change_pct !== undefined && (
                        <span>
                          {finding.direction === 'positive' ? 'Increased' : 'Decreased'} by{' '}
                          <span className="font-semibold">{Math.abs(finding.change_pct).toFixed(1)}%</span>
                        </span>
                      )}
                      {finding.assessment && (
                        <span>
                          Performance is <span className="font-semibold">{finding.assessment}</span>
                          {finding.value !== undefined && ` at ${finding.value.toFixed(1)}%`}
                        </span>
                      )}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {data.recommendations.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Recommendations</h4>
            <ul className="space-y-2">
              {data.recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <ChevronRight className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-700">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Generated timestamp */}
        <div className="text-xs text-gray-500 text-right">
          Generated {new Date(data.generated_at).toLocaleString()}
        </div>
      </CardContent>
    </Card>
  )
}