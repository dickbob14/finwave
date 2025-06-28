"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Download, FileText, Calendar, Eye } from "lucide-react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"

const mockReports = [
  {
    id: "1",
    title: "Q4 2024 Board Package",
    period: "2024-Q4",
    generated_at: "2024-01-15T10:30:00Z",
    status: "completed",
    pages: 24,
    size: "2.4 MB",
  },
  {
    id: "2",
    title: "Q3 2024 Board Package",
    period: "2024-Q3",
    generated_at: "2024-10-15T14:20:00Z",
    status: "completed",
    pages: 22,
    size: "2.1 MB",
  },
  {
    id: "3",
    title: "Q2 2024 Board Package",
    period: "2024-Q2",
    generated_at: "2024-07-15T09:15:00Z",
    status: "completed",
    pages: 20,
    size: "1.9 MB",
  },
  {
    id: "4",
    title: "Q1 2024 Board Package",
    period: "2024-Q1",
    generated_at: "2024-04-15T11:45:00Z",
    status: "completed",
    pages: 18,
    size: "1.7 MB",
  },
]

export default function ReportsHistoryPage() {
  const [showGenerator, setShowGenerator] = useState(false)
  const [selectedPeriod, setSelectedPeriod] = useState("2024-Q4")
  const [generating, setGenerating] = useState(false)

  const handleDownload = (reportId: string, title: string) => {
    // Simulate download
    const link = document.createElement("a")
    link.href = `/placeholder.pdf?height=800&width=600&query=${encodeURIComponent(title)}`
    link.download = `${title.replace(/\s+/g, "-")}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleGenerate = async () => {
    setGenerating(true)
    // Simulate report generation
    await new Promise((resolve) => setTimeout(resolve, 3000))
    setGenerating(false)
    setShowGenerator(false)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-primary">Board Pack History</h1>
          <p className="text-muted-foreground mt-2">Download and manage your generated board packages</p>
        </div>
        <Dialog open={showGenerator} onOpenChange={setShowGenerator}>
          <DialogTrigger asChild>
            <Button className="bg-secondary hover:bg-secondary/90">
              <FileText className="w-4 h-4 mr-2" />
              Generate New Report
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Generate Board Package</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Select Period</label>
                <select
                  className="w-full mt-1 p-2 border rounded-md"
                  value={selectedPeriod}
                  onChange={(e) => setSelectedPeriod(e.target.value)}
                >
                  <option value="2024-Q4">Q4 2024</option>
                  <option value="2024-Q3">Q3 2024</option>
                  <option value="2024-Q2">Q2 2024</option>
                  <option value="2024-Q1">Q1 2024</option>
                </select>
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowGenerator(false)}>
                  Cancel
                </Button>
                <Button onClick={handleGenerate} disabled={generating}>
                  {generating ? "Generating..." : "Generate Report"}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockReports.map((report) => (
          <Card key={report.id} className="relative">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg mb-2">{report.title}</CardTitle>
                  <CardDescription className="space-y-1">
                    <div className="flex items-center text-sm">
                      <Calendar className="h-4 w-4 mr-1" />
                      {new Date(report.generated_at).toLocaleDateString()}
                    </div>
                  </CardDescription>
                </div>
                <Badge className="bg-success text-white">{report.status}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>Pages:</span>
                  <span className="font-medium">{report.pages}</span>
                </div>
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>Size:</span>
                  <span className="font-medium">{report.size}</span>
                </div>
                <div className="flex space-x-2 pt-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1"
                    onClick={() => handleDownload(report.id, report.title)}
                  >
                    <Download className="w-4 h-4 mr-1" />
                    Download
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      window.open(
                        `/placeholder.pdf?height=800&width=600&query=${encodeURIComponent(report.title)}`,
                        "_blank",
                      )
                    }
                  >
                    <Eye className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {mockReports.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No reports generated yet</h3>
            <p className="text-muted-foreground mb-4">Generate your first board package to get started.</p>
            <Button onClick={() => setShowGenerator(true)}>Generate Report</Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
