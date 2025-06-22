import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useSWR from 'swr';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Database,
  Users,
  DollarSign,
  FileText,
  ArrowRight,
  CheckCircle,
  Sparkles,
  Play
} from 'lucide-react';
import { ConnectDataSource } from '@/components/connect-data-source';
import { useToast } from '@/components/ui/use-toast';
import { fetcher } from '@/lib/utils';

interface FirstRunWizardProps {
  workspaceId: string;
  onComplete: () => void;
}

const DEMO_GIF_URL = '/static/finwave-demo.gif';

const SETUP_STEPS = [
  {
    id: 'connect',
    title: 'Connect Your Data',
    description: 'Link your accounting, CRM, and payroll systems',
    icon: <Database className="h-8 w-8" />
  },
  {
    id: 'sync',
    title: 'Sync & Process',
    description: 'We\'ll import your historical data and calculate metrics',
    icon: <Sparkles className="h-8 w-8" />
  },
  {
    id: 'generate',
    title: 'Generate Report',
    description: 'Create your first board-ready PDF in one click',
    icon: <FileText className="h-8 w-8" />
  }
];

export function FirstRunWizard({ workspaceId, onComplete }: FirstRunWizardProps) {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [currentStep, setCurrentStep] = useState(0);
  const [showConnector, setShowConnector] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Check metric count
  const { data: metrics } = useSWR(
    `/api/${workspaceId}/metrics/count`,
    fetcher,
    { refreshInterval: 5000 } // Poll every 5s during setup
  );
  
  // Check integrations
  const { data: integrations } = useSWR(
    `/api/${workspaceId}/oauth/integrations`,
    fetcher,
    { refreshInterval: 5000 }
  );
  
  const hasData = metrics?.count > 0;
  const hasIntegrations = integrations?.length > 0;
  
  // Auto-advance steps
  React.useEffect(() => {
    if (hasIntegrations && currentStep === 0) {
      setCurrentStep(1);
    }
    if (hasData && currentStep === 1) {
      setCurrentStep(2);
    }
  }, [hasIntegrations, hasData, currentStep]);
  
  const handleGenerateReport = async () => {
    setIsGenerating(true);
    
    try {
      // Generate first report
      const response = await fetch(
        `/api/${workspaceId}/reports/board-pack.pdf`,
        {
          headers: {
            'Accept': 'application/pdf'
          }
        }
      );
      
      if (!response.ok) throw new Error('Failed to generate report');
      
      const blob = await response.blob();
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Board_Report_${new Date().toISOString().slice(0, 7)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      // Show success toast
      toast({
        title: "🎉 All set!",
        description: "Your first board report is ready. Share this with your board?",
        action: (
          <Button size="sm" onClick={() => navigate('/share')}>
            Share
          </Button>
        ),
      });
      
      // Mark wizard complete
      setTimeout(() => {
        onComplete();
      }, 2000);
      
    } catch (error) {
      toast({
        title: "Generation failed",
        description: "Please try again or contact support",
        variant: "destructive"
      });
    } finally {
      setIsGenerating(false);
    }
  };
  
  const getStepProgress = () => {
    if (currentStep === 0) return hasIntegrations ? 100 : 0;
    if (currentStep === 1) return hasData ? 100 : hasIntegrations ? 50 : 0;
    if (currentStep === 2) return isGenerating ? 50 : hasData ? 100 : 0;
    return 0;
  };
  
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">Welcome to FinWave! 🚀</h1>
        <p className="text-lg text-muted-foreground">
          Let's get your financial analytics up and running in just 3 steps
        </p>
      </div>
      
      {/* Demo GIF */}
      <Card>
        <CardContent className="p-0">
          <div className="relative aspect-video bg-muted rounded-lg overflow-hidden">
            <img 
              src={DEMO_GIF_URL} 
              alt="FinWave Demo" 
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent flex items-end p-6">
              <div className="text-white">
                <h3 className="text-xl font-semibold mb-1">See FinWave in Action</h3>
                <p className="text-sm opacity-90">
                  From data connection to board report in minutes
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Progress Steps */}
      <div className="space-y-6">
        {SETUP_STEPS.map((step, index) => {
          const isActive = index === currentStep;
          const isComplete = index < currentStep || 
            (index === 0 && hasIntegrations) ||
            (index === 1 && hasData);
          
          return (
            <Card 
              key={step.id} 
              className={`transition-all ${
                isActive ? 'ring-2 ring-primary' : ''
              } ${isComplete ? 'opacity-75' : ''}`}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className={`p-3 rounded-lg ${
                      isComplete ? 'bg-green-100 text-green-600' :
                      isActive ? 'bg-primary/10 text-primary' :
                      'bg-muted'
                    }`}>
                      {isComplete ? (
                        <CheckCircle className="h-8 w-8" />
                      ) : (
                        step.icon
                      )}
                    </div>
                    <div>
                      <CardTitle className="text-xl">
                        Step {index + 1}: {step.title}
                      </CardTitle>
                      <CardDescription className="mt-1">
                        {step.description}
                      </CardDescription>
                    </div>
                  </div>
                  {isComplete && (
                    <Badge variant="success">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Complete
                    </Badge>
                  )}
                </div>
              </CardHeader>
              
              {isActive && (
                <CardContent>
                  <Separator className="mb-4" />
                  
                  {/* Step 1: Connect Data */}
                  {index === 0 && (
                    <div className="space-y-4">
                      <p className="text-sm text-muted-foreground">
                        Connect at least one data source to get started. We recommend starting with your accounting system.
                      </p>
                      
                      <div className="grid gap-4 md:grid-cols-3">
                        <Card className="cursor-pointer hover:border-primary transition-colors"
                              onClick={() => setShowConnector(true)}>
                          <CardContent className="pt-6">
                            <Database className="h-10 w-10 mb-3 text-green-600" />
                            <h4 className="font-medium">QuickBooks</h4>
                            <p className="text-xs text-muted-foreground mt-1">
                              P&L, Balance Sheet, AR/AP
                            </p>
                          </CardContent>
                        </Card>
                        
                        <Card className="cursor-pointer hover:border-primary transition-colors"
                              onClick={() => setShowConnector(true)}>
                          <CardContent className="pt-6">
                            <Users className="h-10 w-10 mb-3 text-blue-600" />
                            <h4 className="font-medium">Salesforce</h4>
                            <p className="text-xs text-muted-foreground mt-1">
                              Pipeline, Bookings, CAC
                            </p>
                          </CardContent>
                        </Card>
                        
                        <Card className="cursor-pointer hover:border-primary transition-colors"
                              onClick={() => setShowConnector(true)}>
                          <CardContent className="pt-6">
                            <DollarSign className="h-10 w-10 mb-3 text-purple-600" />
                            <h4 className="font-medium">Gusto</h4>
                            <p className="text-xs text-muted-foreground mt-1">
                              Headcount, Payroll, Benefits
                            </p>
                          </CardContent>
                        </Card>
                      </div>
                      
                      <Button 
                        className="w-full" 
                        size="lg"
                        onClick={() => setShowConnector(true)}
                      >
                        Connect Your First Data Source
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </Button>
                    </div>
                  )}
                  
                  {/* Step 2: Sync Data */}
                  {index === 1 && (
                    <div className="space-y-4">
                      <Alert>
                        <Sparkles className="h-4 w-4" />
                        <AlertDescription>
                          Great! We're syncing your data. This usually takes 2-5 minutes depending on data volume.
                        </AlertDescription>
                      </Alert>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Syncing financial data...</span>
                          <span className="text-muted-foreground">
                            {metrics?.count || 0} metrics imported
                          </span>
                        </div>
                        <Progress value={getStepProgress()} className="h-2" />
                      </div>
                      
                      <p className="text-sm text-muted-foreground">
                        We're importing your historical data and calculating key metrics like revenue trends, 
                        burn rate, runway, and more. You'll see variance alerts appear automatically.
                      </p>
                    </div>
                  )}
                  
                  {/* Step 3: Generate Report */}
                  {index === 2 && (
                    <div className="space-y-4">
                      <Alert className="border-green-200 bg-green-50">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <AlertDescription>
                          Excellent! Your data is ready. Generate your first board report with one click.
                        </AlertDescription>
                      </Alert>
                      
                      <div className="bg-muted/50 p-4 rounded-lg">
                        <h4 className="font-medium mb-2">Your report will include:</h4>
                        <ul className="space-y-1 text-sm text-muted-foreground">
                          <li>• Executive summary with AI insights</li>
                          <li>• KPI dashboard with trends</li>
                          <li>• Complete financial statements</li>
                          <li>• Variance analysis and alerts</li>
                          <li>• 12-month forecast and runway</li>
                        </ul>
                      </div>
                      
                      <Button 
                        className="w-full" 
                        size="lg"
                        onClick={handleGenerateReport}
                        disabled={isGenerating}
                      >
                        {isGenerating ? (
                          <>
                            <Sparkles className="mr-2 h-4 w-4 animate-spin" />
                            Generating Your First Report...
                          </>
                        ) : (
                          <>
                            Generate Board Report
                            <FileText className="ml-2 h-4 w-4" />
                          </>
                        )}
                      </Button>
                    </div>
                  )}
                </CardContent>
              )}
            </Card>
          );
        })}
      </div>
      
      {/* Skip Link */}
      <div className="text-center">
        <Button 
          variant="link" 
          onClick={onComplete}
          className="text-muted-foreground"
        >
          Skip setup and explore on my own
        </Button>
      </div>
      
      {/* Connect Data Source Modal */}
      <ConnectDataSource
        open={showConnector}
        onOpenChange={setShowConnector}
        workspaceId={workspaceId}
      />
    </div>
  );
}