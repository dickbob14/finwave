"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useAsk } from "@/hooks/useAsk"
import { ChatBubble } from "@/components/ChatBubble"
import { SuggestedQuestions } from "@/components/SuggestedQuestions"
import { Send, Sparkles } from "lucide-react"

export default function AskPage() {
  const [query, setQuery] = useState("")
  const [showSuggestions, setShowSuggestions] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { messages, isStreaming, sendMessage, clearMessages } = useAsk()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || isStreaming) return

    setShowSuggestions(false)
    await sendMessage(query)
    setQuery("")
  }

  const handleSuggestedQuestion = (question: string) => {
    setQuery(question)
    setShowSuggestions(false)
    sendMessage(question)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col h-[calc(100vh-12rem)]">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-gradient-primary p-2 rounded-lg">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-primary">Ask FinWave</h1>
          </div>
          <p className="text-muted-foreground">
            Get instant insights from your QuickBooks, Salesforce, Gusto, and other connected data sources
          </p>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-hidden">
          {showSuggestions && messages.length === 0 ? (
            <SuggestedQuestions onQuestionSelect={handleSuggestedQuestion} />
          ) : (
            <div className="h-full overflow-y-auto space-y-4 pb-4">
              {messages.map((message, index) => (
                <ChatBubble key={index} message={message} />
              ))}
              {isStreaming && (
                <div className="flex items-center gap-2 text-secondary">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-secondary"></div>
                  <span className="text-sm">FinWave is thinking...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t pt-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask about your financial data... (e.g., 'Why is our burn rate increasing?')"
              className="flex-1"
              disabled={isStreaming}
            />
            <Button
              type="submit"
              disabled={!query.trim() || isStreaming}
              className="bg-secondary hover:bg-secondary/90"
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>

          {/* Quick Actions */}
          <div className="flex gap-2 mt-3">
            <Button variant="outline" size="sm" onClick={() => setQuery("/metrics revenue growth")} className="text-xs">
              /metrics
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setQuery("/drivers what affects our burn rate")}
              className="text-xs"
            >
              /drivers
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setQuery("/alerts show critical variances")}
              className="text-xs"
            >
              /alerts
            </Button>
            {messages.length > 0 && (
              <Button variant="outline" size="sm" onClick={clearMessages} className="text-xs ml-auto">
                Clear Chat
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
