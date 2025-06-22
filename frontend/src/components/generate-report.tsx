import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useSWR, { mutate } from 'swr';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  FileText,
  Download,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  Calendar,
  FileDown
} from 'lucide-react';
import { fetcher } from '@/lib/utils';
import { format } from 'date-fns';

interface GenerateReportProps {
  workspaceId: string;
}

interface ReportHistory {
  id: string;
  period: string;
  generated_at: string;
  generated_by: string;
  size_bytes: number;
  download_url: string;
}

export function GenerateReport({ workspaceId }: GenerateReportProps) {
  const [showDialog, setShowDialog] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState(
    format(new Date(), 'yyyy-MM')
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  // Fetch report history
  const { data: historyData, error: historyError } = useSWR(
    `/api/${workspaceId}/reports/history`,
    fetcher
  );
  
  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setProgress(0);
    
    try {
      // Start SSE connection for progress
      const eventSource = new EventSource(
        `/api/${workspaceId}/reports/board-pack/progress`
      );
      
      eventSource.addEventListener('progress', (event) => {
        const data = JSON.parse(event.data);
        setProgress(data.progress);
        setProgressMessage(data.message);
      });
      
      eventSource.addEventListener('complete', async (event) => {
        const data = JSON.parse(event.data);
        eventSource.close();
        
        // Download the PDF
        const response = await fetch(data.download_url);
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Board_Report_${selectedPeriod}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        // Refresh history
        mutate(`/api/${workspaceId}/reports/history`);
        
        setIsGenerating(false);
        setShowDialog(false);
      });
      
      eventSource.addEventListener('error', (event) => {
        eventSource.close();
        setError('Failed to generate report');
        setIsGenerating(false);
      });
      
      // Trigger generation
      await fetch(`/api/${workspaceId}/reports/board-pack.pdf?period=${selectedPeriod}`);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
      setIsGenerating(false);
    }
  };
  
  const handleDownload = async (downloadUrl: string) => {
    try {
      const response = await fetch(downloadUrl);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = downloadUrl.split('/').pop() || 'report.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
    }
  };
  
  const formatFileSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };
  
  // Generate period options (last 12 months)
  const periodOptions = Array.from({ length: 12 }, (_, i) => {
    const date = new Date();
    date.setMonth(date.getMonth() - i);
    return {
      value: format(date, 'yyyy-MM'),
      label: format(date, 'MMMM yyyy')
    };
  });
  
  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Board Reports</CardTitle>
              <CardDescription>
                Generate comprehensive PDF reports for board meetings
              </CardDescription>
            </div>
            <Button onClick={() => setShowDialog(true)}>
              <FileText className="h-4 w-4 mr-2" />
              Generate Report
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="history" className="w-full">
            <TabsList>
              <TabsTrigger value="history">Report History</TabsTrigger>
              <TabsTrigger value="templates">Templates</TabsTrigger>
            </TabsList>
            
            <TabsContent value="history" className="mt-4">
              {historyError ? (
                <div className="text-center py-8 text-muted-foreground">
                  Failed to load report history
                </div>
              ) : !historyData ? (
                <div className="text-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto" />
                </div>
              ) : historyData.reports.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No reports generated yet
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Period</TableHead>
                      <TableHead>Generated</TableHead>
                      <TableHead>Generated By</TableHead>
                      <TableHead>Size</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {historyData.reports.map((report: ReportHistory) => (
                      <TableRow key={report.id}>
                        <TableCell className="font-medium">
                          {format(new Date(report.period + '-01'), 'MMMM yyyy')}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-muted-foreground" />
                            {format(new Date(report.generated_at), 'MMM d, yyyy h:mm a')}
                          </div>
                        </TableCell>
                        <TableCell>{report.generated_by}</TableCell>
                        <TableCell>{formatFileSize(report.size_bytes)}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownload(report.download_url)}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </TabsContent>
            
            <TabsContent value="templates" className="mt-4 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Board Report Pack</CardTitle>
                  <CardDescription>
                    Comprehensive monthly board report with financials, KPIs, and analysis
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="text-sm">Executive Summary with AI insights</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="text-sm">KPI Dashboard with trends</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="text-sm">Financial Statements (P&L, BS, CF)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="text-sm">Variance Analysis with alerts</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="text-sm">12-Month Forecast & Runway</span>
                    </div>
                  </div>
                  <div className="mt-4">
                    <Badge>Default Template</Badge>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
      
      {/* Generate Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Generate Board Report</DialogTitle>
            <DialogDescription>
              Select the period for your board report
            </DialogDescription>
          </DialogHeader>
          
          {!isGenerating ? (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Report Period</label>
                <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {periodOptions.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {error && (
                <div className="flex items-center gap-2 text-red-600">
                  <XCircle className="h-4 w-4" />
                  <span className="text-sm">{error}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4 py-8">
              <div className="text-center">
                <FileText className="h-12 w-12 mx-auto mb-4 text-primary animate-pulse" />
                <Progress value={progress} className="mb-2" />
                <p className="text-sm text-muted-foreground">{progressMessage}</p>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleGenerate} 
              disabled={isGenerating}
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <FileDown className="h-4 w-4 mr-2" />
                  Generate PDF
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}