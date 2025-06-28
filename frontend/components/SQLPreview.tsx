"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Copy, ChevronDown, ChevronRight, Database } from "lucide-react"
import { toast } from "sonner"

interface SQLPreviewProps {
  sql: string
  title?: string
}

export function SQLPreview({ sql, title = "Query Used" }: SQLPreviewProps) {
  const [isOpen, setIsOpen] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(sql)
    toast.success("SQL copied to clipboard")
  }

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className="border-dashed">
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                <Database className="h-4 w-4 text-accent" />
                {title}
              </CardTitle>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleCopy()
                  }}
                >
                  <Copy className="h-3 w-3" />
                </Button>
                {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </div>
            </div>
            <CardDescription className="text-xs">
              Click to view the SQL query that generated this analysis
            </CardDescription>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0">
            <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
              <code className="text-foreground">{sql}</code>
            </pre>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  )
}
