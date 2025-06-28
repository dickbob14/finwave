"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"

const mockChartData = [
  { month: "Jan", base: 100000, aggressive: 120000, downside: 80000 },
  { month: "Feb", base: 105000, aggressive: 130000, downside: 85000 },
  { month: "Mar", base: 110000, aggressive: 140000, downside: 90000 },
  { month: "Apr", base: 115000, aggressive: 150000, downside: 95000 },
  { month: "May", base: 120000, aggressive: 160000, downside: 100000 },
  { month: "Jun", base: 125000, aggressive: 170000, downside: 105000 },
]

export default function ScenarioPlanningPage() {
  const [selectedScenario, setSelectedScenario] = useState("base")
  const [drivers, setDrivers] = useState({
    revenue_growth: [15],
    cost_reduction: [5],
    headcount_growth: [10],
    marketing_spend: [20],
  })

  const handleDriverChange = (driverId: string, value: number[]) => {
    setDrivers((prev) => ({
      ...prev,
      [driverId]: value,
    }))
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-primary">Scenario Planning</h1>
          <p className="text-muted-foreground mt-2">Model different business scenarios and their financial impact</p>
        </div>
        <Button className="bg-secondary hover:bg-secondary/90">Save Scenario</Button>
      </div>

      <Tabs defaultValue="drivers" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="drivers">Business Drivers</TabsTrigger>
          <TabsTrigger value="scenarios">Scenario Comparison</TabsTrigger>
          <TabsTrigger value="forecast">Forecast Results</TabsTrigger>
        </TabsList>

        <TabsContent value="drivers" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Revenue Growth Rate</CardTitle>
                <CardDescription>Annual revenue growth percentage</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>0%</span>
                  <span className="font-semibold text-primary">{drivers.revenue_growth[0]}%</span>
                  <span>50%</span>
                </div>
                <Slider
                  value={drivers.revenue_growth}
                  onValueChange={(value) => handleDriverChange("revenue_growth", value)}
                  max={50}
                  step={1}
                  className="w-full"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cost Reduction</CardTitle>
                <CardDescription>Operating cost reduction percentage</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>0%</span>
                  <span className="font-semibold text-primary">{drivers.cost_reduction[0]}%</span>
                  <span>25%</span>
                </div>
                <Slider
                  value={drivers.cost_reduction}
                  onValueChange={(value) => handleDriverChange("cost_reduction", value)}
                  max={25}
                  step={1}
                  className="w-full"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Headcount Growth</CardTitle>
                <CardDescription>Employee headcount growth percentage</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>0%</span>
                  <span className="font-semibold text-primary">{drivers.headcount_growth[0]}%</span>
                  <span>30%</span>
                </div>
                <Slider
                  value={drivers.headcount_growth}
                  onValueChange={(value) => handleDriverChange("headcount_growth", value)}
                  max={30}
                  step={1}
                  className="w-full"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Marketing Spend</CardTitle>
                <CardDescription>Marketing budget as % of revenue</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>0%</span>
                  <span className="font-semibold text-primary">{drivers.marketing_spend[0]}%</span>
                  <span>40%</span>
                </div>
                <Slider
                  value={drivers.marketing_spend}
                  onValueChange={(value) => handleDriverChange("marketing_spend", value)}
                  max={40}
                  step={1}
                  className="w-full"
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="scenarios" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { id: "base", name: "Base Case", description: "Conservative growth assumptions" },
              { id: "aggressive", name: "Aggressive", description: "Optimistic growth scenario" },
              { id: "downside", name: "Downside", description: "Conservative/risk scenario" },
            ].map((scenario) => (
              <Card
                key={scenario.id}
                className={`cursor-pointer transition-all ${
                  selectedScenario === scenario.id ? "ring-2 ring-secondary" : ""
                }`}
                onClick={() => setSelectedScenario(scenario.id)}
              >
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-lg">{scenario.name}</CardTitle>
                    {selectedScenario === scenario.id && <Badge className="bg-secondary">Selected</Badge>}
                  </div>
                  <CardDescription>{scenario.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Revenue Growth:</span>
                      <span className="font-semibold">
                        {scenario.id === "base" ? "15%" : scenario.id === "aggressive" ? "25%" : "8%"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Cost Reduction:</span>
                      <span className="font-semibold">
                        {scenario.id === "base" ? "5%" : scenario.id === "aggressive" ? "10%" : "2%"}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="forecast" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Revenue Forecast Comparison</CardTitle>
              <CardDescription>Compare revenue projections across different scenarios</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={mockChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, ""]} />
                    <Legend />
                    <Line type="monotone" dataKey="base" stroke="#1E2A38" strokeWidth={2} name="Base Case" />
                    <Line type="monotone" dataKey="aggressive" stroke="#10B981" strokeWidth={2} name="Aggressive" />
                    <Line type="monotone" dataKey="downside" stroke="#F87171" strokeWidth={2} name="Downside" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
