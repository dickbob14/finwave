// Example: Update Templates page to fetch from metric store
// File: frontend/src/app/templates/page.tsx

// Add this hook to fetch metrics alongside templates
const useMetrics = (workspaceId: string, templateName?: string) => {
  const { data, error, isLoading } = useSWR(
    templateName ? `${API_BASE}/${workspaceId}/metrics/summary` : null,
    fetcher,
    { refreshInterval: 30000 }
  )
  
  return {
    metrics: data?.metrics || {},
    period: data?.period,
    isLoading,
    error
  }
}

// In the component, add metrics display:
export default function TemplatesPage() {
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  const { metrics, period } = useMetrics('demo', selectedTemplate)
  
  // ... existing code ...
  
  // Add metrics display to each template card
  return (
    <Card key={template.name}>
      {/* ... existing card content ... */}
      
      {/* Add metrics summary if available */}
      {template.recent_files?.[0] && metrics.revenue && (
        <CardContent className="pt-0">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Revenue</span>
              <span className="font-medium">${(metrics.revenue?.value || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">EBITDA</span>
              <span className="font-medium">${(metrics.ebitda?.value || 0).toLocaleString()}</span>
            </div>
            {metrics.mrr && (
              <div className="flex justify-between">
                <span className="text-gray-600">MRR</span>
                <span className="font-medium">${(metrics.mrr.value || 0).toLocaleString()}</span>
              </div>
            )}
            {metrics.burn_rate && (
              <div className="flex justify-between">
                <span className="text-gray-600">Burn Rate</span>
                <span className="font-medium">${(metrics.burn_rate.value || 0).toLocaleString()}/mo</span>
              </div>
            )}
          </div>
          {period && (
            <div className="text-xs text-gray-500 mt-2">
              As of {new Date(period).toLocaleDateString()}
            </div>
          )}
        </CardContent>
      )}
      
      {/* ... rest of card ... */}
    </Card>
  )
}