"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { ExternalLink, FileText, Database, BarChart3 } from "lucide-react"

interface Citation {
  id: string
  source: string
  snippet: string
  url?: string
  type?: "sql" | "document" | "api" | "metric"
}

interface CitationPopoverProps {
  citation: Citation
  index: number
}

export function CitationPopover({ citation, index }: CitationPopoverProps) {
  const [open, setOpen] = useState(false)

  const getSourceIcon = (source: string, type?: string) => {
    if (type === "sql") return Database
    if (type === "metric") return BarChart3
    if (source.toLowerCase().includes("quickbooks")) return FileText
    if (source.toLowerCase().includes("salesforce")) return BarChart3
    return FileText
  }

  const getSourceColor = (source: string) => {
    if (source.toLowerCase().includes("quickbooks")) return "bg-green-100 text-green-800"
    if (source.toLowerCase().includes("salesforce")) return "bg-blue-100 text-blue-800"
    if (source.toLowerCase().includes("gusto")) return "bg-purple-100 text-purple-800"
    return "bg-gray-100 text-gray-800"
  }

  const Icon = getSourceIcon(citation.source, citation.type)

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Badge variant="outline" className="cursor-pointer hover:bg-accent hover:text-white transition-colors">
          <Icon className="h-3 w-3 mr-1" />
          {index}
        </Badge>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="start">
        <Card className="border-0 shadow-none">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                <Icon className="h-4 w-4" />
                Source {index}
              </CardTitle>
              <Badge className={getSourceColor(citation.source)}>{citation.source}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <CardDescription className="text-sm leading-relaxed">{citation.snippet}</CardDescription>

            {citation.url && (
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => window.open(citation.url, "_blank")}
              >
                <ExternalLink className="h-3 w-3 mr-2" />
                View Source
              </Button>
            )}
          </CardContent>
        </Card>
      </PopoverContent>
    </Popover>
  )
}
