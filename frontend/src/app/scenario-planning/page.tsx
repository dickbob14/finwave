"use client"

import React from 'react'
import { ScenarioPlanner } from '@/components/scenario-planner'

export default function ScenarioPlanningPage() {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Scenario Planning</h1>
        <p className="text-muted-foreground mt-1">
          Test what-if scenarios and see the impact on your financial projections
        </p>
      </div>
      
      <ScenarioPlanner workspaceId="demo" />
    </div>
  )
}