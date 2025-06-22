"use client"

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ConnectDataSource } from '@/components/connect-data-source'
import { 
  ArrowRight, 
  BarChart3, 
  FileText, 
  Zap, 
  Shield, 
  TrendingUp,
  Database,
  CheckCircle
} from 'lucide-react'

export default function HomePage() {
  const router = useRouter()
  const [showConnector, setShowConnector] = useState(false)
  const [hasIntegrations, setHasIntegrations] = useState(false)
  
  // Check if user has integrations
  useEffect(() => {
    const checkIntegrations = async () => {
      try {
        const res = await fetch('/api/demo/oauth/integrations')
        if (res.ok) {
          const data = await res.json()
          setHasIntegrations(data.length > 0)
        }
      } catch (error) {
        console.error('Failed to check integrations:', error)
      }
    }
    
    checkIntegrations()
  }, [])
  
  // Redirect if already has integrations
  useEffect(() => {
    if (hasIntegrations) {
      router.push('/templates')
    }
  }, [hasIntegrations, router])
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white">
      {/* Hero Section */}
      <div className="container mx-auto px-4 pt-16 pb-12">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Financial Analytics That Work
            <span className="text-primary"> Like Magic</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Connect QuickBooks and get board-ready reports, real-time KPIs, and 
            AI-powered insights in minutes. Built for modern finance teams.
          </p>
          <div className="flex gap-4 justify-center">
            <Button 
              size="lg" 
              onClick={() => setShowConnector(true)}
              className="bg-primary hover:bg-primary-700"
            >
              Connect QuickBooks
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button 
              size="lg" 
              variant="outline"
              onClick={() => router.push('/demo')}
            >
              View Demo
            </Button>
          </div>
        </div>
      </div>
      
      {/* Features Grid */}
      <div className="container mx-auto px-4 py-16">
        <div className="grid md:grid-cols-3 gap-8">
          <Card>
            <CardHeader>
              <div className="h-12 w-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                <FileText className="h-6 w-6 text-primary-600" />
              </div>
              <CardTitle>Board-Ready Reports</CardTitle>
              <CardDescription>
                Generate beautiful PDF reports with financials, KPIs, and variance 
                analysis in one click
              </CardDescription>
            </CardHeader>
          </Card>
          
          <Card>
            <CardHeader>
              <div className="h-12 w-12 bg-secondary-100 rounded-lg flex items-center justify-center mb-4">
                <TrendingUp className="h-6 w-6 text-secondary-600" />
              </div>
              <CardTitle>Real-Time Metrics</CardTitle>
              <CardDescription>
                Track MRR, burn rate, runway, and custom KPIs with automatic 
                variance alerts
              </CardDescription>
            </CardHeader>
          </Card>
          
          <Card>
            <CardHeader>
              <div className="h-12 w-12 bg-accent-100 rounded-lg flex items-center justify-center mb-4">
                <Zap className="h-6 w-6 text-accent-600" />
              </div>
              <CardTitle>AI Insights</CardTitle>
              <CardDescription>
                Get intelligent commentary and recommendations powered by GPT-4
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
      
      {/* How It Works */}
      <div className="bg-gray-50 py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">
            From Data to Insights in 3 Steps
          </h2>
          <div className="max-w-4xl mx-auto">
            <div className="space-y-8">
              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 bg-primary rounded-full flex items-center justify-center text-white font-bold">
                    1
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">Connect Your Data</h3>
                  <p className="text-gray-600">
                    Securely connect QuickBooks, Salesforce, and Gusto. We pull your 
                    financial data automatically.
                  </p>
                </div>
              </div>
              
              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 bg-primary rounded-full flex items-center justify-center text-white font-bold">
                    2
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">Automatic Analysis</h3>
                  <p className="text-gray-600">
                    We calculate key metrics, detect variances, and generate forecasts 
                    using proven financial models.
                  </p>
                </div>
              </div>
              
              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 bg-primary rounded-full flex items-center justify-center text-white font-bold">
                    3
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">Share & Collaborate</h3>
                  <p className="text-gray-600">
                    Generate board reports, share dashboards, and get alerts when 
                    metrics need attention.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Trust Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Built for Finance Teams</h2>
          <p className="text-gray-600">
            Trusted by CFOs and finance leaders at growing companies
          </p>
        </div>
        <div className="grid md:grid-cols-4 gap-8 text-center">
          <div>
            <Shield className="h-8 w-8 text-primary mx-auto mb-2" />
            <h3 className="font-semibold">Bank-Level Security</h3>
            <p className="text-sm text-gray-600">256-bit encryption</p>
          </div>
          <div>
            <Database className="h-8 w-8 text-primary mx-auto mb-2" />
            <h3 className="font-semibold">Real-Time Sync</h3>
            <p className="text-sm text-gray-600">Always up to date</p>
          </div>
          <div>
            <BarChart3 className="h-8 w-8 text-primary mx-auto mb-2" />
            <h3 className="font-semibold">Custom Metrics</h3>
            <p className="text-sm text-gray-600">Track what matters</p>
          </div>
          <div>
            <CheckCircle className="h-8 w-8 text-primary mx-auto mb-2" />
            <h3 className="font-semibold">SOC 2 Compliant</h3>
            <p className="text-sm text-gray-600">Enterprise ready</p>
          </div>
        </div>
      </div>
      
      {/* CTA Section */}
      <div className="bg-primary py-16">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Transform Your Financial Reporting?
          </h2>
          <p className="text-primary-100 mb-8">
            Join finance teams saving 10+ hours per month on reporting
          </p>
          <Button 
            size="lg" 
            variant="secondary"
            onClick={() => setShowConnector(true)}
          >
            Get Started Free
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </div>
      
      {/* Connect Data Source Modal */}
      <ConnectDataSource
        open={showConnector}
        onOpenChange={setShowConnector}
        workspaceId="demo"
      />
    </div>
  )
}
