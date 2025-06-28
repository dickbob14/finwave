"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { CitationPopover } from "./CitationPopover"
import { SQLPreview } from "./SQLPreview"
import { KPITable } from "./KPITable"
import { Copy, User, Bot } from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  citations?: Citation[]
  sql?: string
  kpis?: KPI[]
  timestamp: Date
}

interface Citation {
  id: string
  source: string
  snippet: string
  url?: string
}

interface KPI {
  metric: string
  value: string
  change: string
  trend: "up" | "down" | "neutral"
}

interface ChatBubbleProps {
  message: Message
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === "user"

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    toast.success("Copied to clipboard")
  }

  const renderContentWithCitations = (content: string, citations?: Citation[]) => {
    if (!citations) return content

    let renderedContent = content
    citations.forEach((citation, index) => {
      const citationPattern = new RegExp(`\\[${citation.id}\\]`, "g")
      renderedContent = renderedContent.replace(
        citationPattern,
        `<span class="citation-marker" data-citation-id="${citation.id}">[${index + 1}]</span>`,
      )
    })

    return (
      <div
        dangerouslySetInnerHTML={{ __html: renderedContent }}
        className="prose prose-sm max-w-none [&_.citation-marker]:inline-block [&_.citation-marker]:bg-accent [&_.citation-marker]:text-white [&_.citation-marker]:px-1 [&_.citation-marker]:py-0.5 [&_.citation-marker]:rounded [&_.citation-marker]:text-xs [&_.citation-marker]:cursor-pointer [&_.citation-marker]:hover:bg-accent/80"
      />
    )
  }

  return (
    <div className={cn("flex gap-3", isUser ? "justify-end" : "justify-start")}>
      <div className={cn("flex gap-3 max-w-4xl", isUser ? "flex-row-reverse" : "flex-row")}>
        {/* Avatar */}
        <div
          className={cn(
            "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
            isUser ? "bg-primary text-white" : "bg-secondary text-white",
          )}
        >
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </div>

        {/* Message Content */}
        <Card
          className={cn("flex-1", isUser ? "bg-primary/5 border-primary/20" : "bg-secondary/5 border-secondary/20")}
        >
          <CardContent className="p-4">
            <div className="space-y-3">
              {/* Main Content */}
              <div className="text-sm leading-relaxed">
                {renderContentWithCitations(message.content, message.citations)}
              </div>

              {/* KPI Table */}
              {message.kpis && <KPITable kpis={message.kpis} />}

              {/* SQL Preview */}
              {message.sql && <SQLPreview sql={message.sql} />}

              {/* Citations */}
              {message.citations && message.citations.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-muted-foreground">Sources:</h4>
                  <div className="flex flex-wrap gap-2">
                    {message.citations.map((citation, index) => (
                      <CitationPopover key={citation.id} citation={citation} index={index + 1} />
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center justify-between pt-2 border-t border-muted">
                <span className="text-xs text-muted-foreground">{message.timestamp.toLocaleTimeString()}</span>
                <Button variant="ghost" size="sm" onClick={handleCopy}>
                  <Copy className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
