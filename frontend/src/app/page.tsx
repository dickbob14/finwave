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
    <div className="min-h-screen">
      {/* Hero Section with gradient background */}
      <div className="bg-gradient-primary relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-white/10"></div>
        <div className="container mx-auto px-4 pt-16 pb-20 relative z-10">
          <div className="text-center max-w-4xl mx-auto">
            <h1 className="text-5xl font-display font-bold text-white mb-6">
              Financial Analytics That Work
              <span className="block mt-2"> Like Magic</span>
            </h1>
            <p className="text-xl text-white/90 mb-8">
              Connect QuickBooks and get board-ready reports, real-time KPIs, and 
              AI-powered insights in minutes. Built for modern finance teams.
            </p>
            <div className="flex gap-4 justify-center">
              <Button 
                size="lg" 
                onClick={() => setShowConnector(true)}
                className="bg-white text-navy hover:bg-cloud font-semibold shadow-lg hover:shadow-xl transition-all"
              >
                Connect QuickBooks
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button 
                size="lg" 
                variant="outline"
                onClick={() => router.push('/demo')}
                className="border-white text-white hover:bg-white/10"
              >
                View Demo
              </Button>
            </div>
          </div>
        </div>
        
        {/* Wave decoration */}
        <svg className="absolute bottom-0 left-0 w-full" viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0 60C240 120 480 0 720 60C960 120 1200 0 1440 60V120H0V60Z" fill="#F9FAFB"/>
        </svg>
      </div>
      
      {/* Features Grid */}
      <div className="container mx-auto px-4 py-16">
        <div className="grid md:grid-cols-3 gap-8">
          <Card className="card-shadow hover:card-shadow-hover transition-all duration-200 border-mist">
            <CardHeader>
              <div className="h-12 w-12 bg-navy/10 rounded-lg flex items-center justify-center mb-4">
                <FileText className="h-6 w-6 text-navy" />
              </div>
              <CardTitle className="text-navy">Board-Ready Reports</CardTitle>
              <CardDescription className="text-navy/70">
                Generate beautiful PDF reports with financials, KPIs, and variance 
                analysis in one click
              </CardDescription>
            </CardHeader>
          </Card>
          
          <Card className="card-shadow hover:card-shadow-hover transition-all duration-200 border-mist">
            <CardHeader>
              <div className="h-12 w-12 bg-teal/10 rounded-lg flex items-center justify-center mb-4">
                <TrendingUp className="h-6 w-6 text-teal" />
              </div>
              <CardTitle className="text-navy">Real-Time Metrics</CardTitle>
              <CardDescription className="text-navy/70">
                Track MRR, burn rate, runway, and custom KPIs with automatic 
                variance alerts
              </CardDescription>
            </CardHeader>
          </Card>
          
          <Card className="card-shadow hover:card-shadow-hover transition-all duration-200 border-mist">
            <CardHeader>
              <div className="h-12 w-12 bg-indigo/10 rounded-lg flex items-center justify-center mb-4">
                <Zap className="h-6 w-6 text-indigo" />
              </div>
              <CardTitle className="text-navy">AI Insights</CardTitle>
              <CardDescription className="text-navy/70">
                Get intelligent commentary and recommendations powered by GPT-4
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
      
      {/* How It Works */}
      <div className="bg-mist/30 py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-display font-bold text-center mb-12 text-navy">
            From Data to Insights in 3 Steps
          </h2>
          <div className="max-w-4xl mx-auto">
            <div className="space-y-8">
              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 bg-teal rounded-full flex items-center justify-center text-white font-bold">
                    1
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2 text-navy">Connect Your Data</h3>
                  <p className="text-navy/70">
                    Securely connect QuickBooks, Salesforce, and Gusto. We pull your 
                    financial data automatically.
                  </p>
                </div>
              </div>
              
              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 bg-teal rounded-full flex items-center justify-center text-white font-bold">
                    2
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2 text-navy">Automatic Analysis</h3>
                  <p className="text-navy/70">
                    We calculate key metrics, detect variances, and generate forecasts 
                    using proven financial models.
                  </p>
                </div>
              </div>
              
              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 bg-teal rounded-full flex items-center justify-center text-white font-bold">
                    3
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2 text-navy">Share & Collaborate</h3>
                  <p className="text-navy/70">
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
          <h2 className="text-3xl font-display font-bold mb-4 text-navy">Built for Finance Teams</h2>
          <p className="text-navy/70">
            Trusted by CFOs and finance leaders at growing companies
          </p>
        </div>
        <div className="grid md:grid-cols-4 gap-8 text-center">
          <div>
            <Shield className="h-8 w-8 text-teal mx-auto mb-2" />
            <h3 className="font-semibold text-navy">Bank-Level Security</h3>
            <p className="text-sm text-navy/70">256-bit encryption</p>
          </div>
          <div>
            <Database className="h-8 w-8 text-teal mx-auto mb-2" />
            <h3 className="font-semibold text-navy">Real-Time Sync</h3>
            <p className="text-sm text-navy/70">Always up to date</p>
          </div>
          <div>
            <BarChart3 className="h-8 w-8 text-teal mx-auto mb-2" />
            <h3 className="font-semibold text-navy">Custom Metrics</h3>
            <p className="text-sm text-navy/70">Track what matters</p>
          </div>
          <div>
            <CheckCircle className="h-8 w-8 text-teal mx-auto mb-2" />
            <h3 className="font-semibold text-navy">SOC 2 Compliant</h3>
            <p className="text-sm text-navy/70">Enterprise ready</p>
          </div>
        </div>
      </div>
      
      {/* CTA Section */}
      <div className="bg-navy py-16">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-display font-bold text-white mb-4">
            Ready to Transform Your Financial Reporting?
          </h2>
          <p className="text-white/80 mb-8">
            Join finance teams saving 10+ hours per month on reporting
          </p>
          <Button 
            size="lg" 
            className="bg-teal hover:bg-teal/90 text-white font-semibold shadow-lg hover:shadow-xl transition-all"
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
