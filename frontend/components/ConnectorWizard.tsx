"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { apiPost } from "@/lib/api"
import { toast } from "sonner"

interface Connector {
  id: string
  name: string
  description: string
  status: "available" | "connected" | "error"
  icon: string
}

const connectors: Connector[] = [
  {
    id: "quickbooks",
    name: "QuickBooks Online",
    description: "Connect your QuickBooks Online account for financial data",
    status: "available",
    icon: "📊",
  },
  {
    id: "salesforce",
    name: "Salesforce",
    description: "Import sales pipeline and customer data",
    status: "available",
    icon: "☁️",
  },
  {
    id: "gusto",
    name: "Gusto",
    description: "Sync payroll and HR data",
    status: "available",
    icon: "👥",
  },
]

export const ConnectorWizard = () => {
  const [connecting, setConnecting] = useState<string | null>(null)

  const handleConnect = async (source: string) => {
    setConnecting(source)
    try {
      const response = await apiPost(`/default/oauth/connect/${source}`)

      // Open OAuth popup
      const popup = window.open(response.auth_url, "oauth", "width=600,height=600,scrollbars=yes,resizable=yes")

      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const integrations = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/oauth/integrations`,
          )
          const data = await integrations.json()

          const integration = data.find((i: any) => i.source === source)
          if (integration && integration.status === "active") {
            clearInterval(pollInterval)
            popup?.close()
            toast.success(`${source} connected successfully!`)
            setConnecting(null)
          }
        } catch (error) {
          // Continue polling
        }
      }, 2000)

      // Clean up if popup is closed manually
      const checkClosed = setInterval(() => {
        if (popup?.closed) {
          clearInterval(pollInterval)
          clearInterval(checkClosed)
          setConnecting(null)
        }
      }, 1000)
    } catch (error) {
      toast.error(`Failed to connect ${source}`)
      setConnecting(null)
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {connectors.map((connector) => (
        <Card key={connector.id} className="relative">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-2xl">{connector.icon}</span>
                <CardTitle className="text-lg">{connector.name}</CardTitle>
              </div>
              <Badge
                variant={connector.status === "connected" ? "default" : "secondary"}
                className={connector.status === "connected" ? "bg-success" : ""}
              >
                {connector.status}
              </Badge>
            </div>
            <CardDescription>{connector.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={() => handleConnect(connector.id)}
              disabled={connecting === connector.id || connector.status === "connected"}
              className="w-full"
              variant={connector.status === "connected" ? "outline" : "default"}
            >
              {connecting === connector.id
                ? "Connecting..."
                : connector.status === "connected"
                  ? "Connected"
                  : "Connect"}
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
