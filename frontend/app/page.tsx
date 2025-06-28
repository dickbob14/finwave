"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ConnectorWizard } from "@/components/ConnectorWizard"
import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { BarChart3, TrendingUp, Users, DollarSign } from "lucide-react"

export default function HomePage() {
  const [showConnector, setShowConnector] = useState(false)

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="bg-gradient-primary text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <div className="flex justify-center mb-8">
              <img
                src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Screenshot%202025-06-22%20at%204.27.55%E2%80%AFAM-dY8s0sTShZgyJNYE8FRwVx6FNoDXqd.png"
                alt="FinWave Logo"
                className="h-20 w-auto"
              />
            </div>
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              Financial Intelligence,
              <br />
              <span className="text-secondary">Simplified</span>
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-white/90 max-w-3xl mx-auto">
              Transform your financial data into actionable insights with AI-powered analytics and automated reporting.
            </p>
            <Dialog open={showConnector} onOpenChange={setShowConnector}>
              <DialogTrigger asChild>
                <Button size="lg" className="bg-white text-primary hover:bg-white/90 text-lg px-8 py-4">
                  Connect QuickBooks
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl">
                <DialogHeader>
                  <DialogTitle>Connect Your Data Sources</DialogTitle>
                </DialogHeader>
                <ConnectorWizard />
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-primary mb-4">Everything you need for financial planning</h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            From real-time dashboards to scenario planning, FinWave provides the tools CFOs need to make informed
            decisions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <Card className="text-center">
            <CardHeader>
              <div className="mx-auto bg-secondary/10 p-3 rounded-full w-fit">
                <BarChart3 className="h-8 w-8 text-secondary" />
              </div>
              <CardTitle>Real-time Dashboards</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Monitor key metrics with live updates from your connected data sources.</CardDescription>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <div className="mx-auto bg-accent/10 p-3 rounded-full w-fit">
                <TrendingUp className="h-8 w-8 text-accent" />
              </div>
              <CardTitle>Scenario Planning</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Model different business scenarios and their financial impact.</CardDescription>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <div className="mx-auto bg-success/10 p-3 rounded-full w-fit">
                <Users className="h-8 w-8 text-success" />
              </div>
              <CardTitle>Smart Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Get notified when metrics deviate from expected ranges.</CardDescription>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <div className="mx-auto bg-primary/10 p-3 rounded-full w-fit">
                <DollarSign className="h-8 w-8 text-primary" />
              </div>
              <CardTitle>Board Reports</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Generate professional board packages with one click.</CardDescription>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-muted">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-primary mb-4">Ready to get started?</h2>
            <p className="text-xl text-muted-foreground mb-8">
              Connect your QuickBooks account and see your financial data come to life.
            </p>
            <Button size="lg" className="bg-secondary hover:bg-secondary/90" onClick={() => setShowConnector(true)}>
              Start Free Trial
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
